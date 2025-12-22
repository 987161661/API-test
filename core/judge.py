import sys
import io
import contextlib
import json
import traceback
from typing import Any

import re

def extract_code(response: str) -> str:
    """Extract code from markdown code blocks."""
    # Match ``` followed by optional language name, then code, then ```
    match = re.search(r"```(?:\w+)?\s*(.*?)```", response, re.DOTALL)
    if match:
        return match.group(1).strip()
    return response.strip()

def run_code_test(model_code: str, test_code: str) -> dict:
    """
    Executes the model's code followed by the test code.
    Returns: {'success': bool, 'output': str, 'error': str}
    WARNING: This executes code locally. In a production env, use a sandbox.
    """
    # Capture stdout
    stdout_capture = io.StringIO()
    
    full_code = f"{model_code}\n\n{test_code}"
    
    try:
        with contextlib.redirect_stdout(stdout_capture):
            # Create a restricted global environment
            # We allow standard built-ins but ideally this should be more restricted
            exec_globals = {"__builtins__": __builtins__}
            exec(full_code, exec_globals)
        
        return {
            "success": True,
            "output": stdout_capture.getvalue(),
            "error": None
        }
    except Exception:
        return {
            "success": False,
            "output": stdout_capture.getvalue(),
            "error": traceback.format_exc()
        }

def evaluate_tool_use(response: str, expected_schema: Any) -> dict:
    """
    Checks if the response contains a valid JSON matching the expected structure.
    expected_schema: The expected JSON object (dict or list).
    """
    try:
        # Extract JSON if wrapped in markdown
        json_str = response
        if "```json" in response:
            json_str = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            json_str = response.split("```")[1].split("```")[0].strip()
        
        data = json.loads(json_str)
        
        # Handle OpenAI style wrapper: {"tool_calls": [...]}
        if isinstance(data, dict) and "tool_calls" in data:
            tool_calls = data["tool_calls"]
            if isinstance(tool_calls, list):
                # Normalize: Extract function info from each call
                cleaned_data = []
                for tc in tool_calls:
                    if "function" in tc:
                        cleaned_data.append(tc["function"])
                    else:
                        cleaned_data.append(tc)
                
                # If we expect a single dict but got a list of 1, take it
                if isinstance(expected_schema, dict) and len(cleaned_data) == 1:
                    data = cleaned_data[0]
                else:
                    data = cleaned_data
        
        # Helper to compare two items
        def compare_items(actual, expected):
            if isinstance(expected, dict):
                if not isinstance(actual, dict):
                    return False, f"Expected dict, got {type(actual)}"
                
                for k, v in expected.items():
                    if k not in actual:
                        return False, f"Missing key: {k}"
                    
                    act_val = actual[k]
                    # Handle stringified arguments
                    if k in ["arguments", "parameters"] and isinstance(v, dict) and isinstance(act_val, str):
                        try:
                            act_val = json.loads(act_val)
                        except:
                            pass
                    
                    if act_val != v:
                        return False, f"Key '{k}' mismatch. Expected {v}, got {act_val}"
                return True, None
            else:
                return (actual == expected), f"Expected {expected}, got {actual}"

        # Main comparison
        if isinstance(expected_schema, list):
            if not isinstance(data, list):
                 return {"success": False, "error": "Expected a list of tool calls"}
            if len(data) != len(expected_schema):
                 return {"success": False, "error": f"Count mismatch. Expected {len(expected_schema)}, got {len(data)}"}
            
            for i, (act, exp) in enumerate(zip(data, expected_schema)):
                ok, err = compare_items(act, exp)
                if not ok:
                    return {"success": False, "error": f"Item {i}: {err}"}
        else:
            ok, err = compare_items(data, expected_schema)
            if not ok:
                 return {"success": False, "error": err}

        return {"success": True, "output": json.dumps(data, indent=2)}
        
    except json.JSONDecodeError:
        return {"success": False, "error": "Invalid JSON format"}
    except Exception as e:
        return {"success": False, "error": str(e)}
