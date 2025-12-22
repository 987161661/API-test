import json
import os
from typing import List, Dict, Optional, Any
from enum import Enum
from .judge import extract_code, run_code_test, evaluate_tool_use

class BenchmarkType(Enum):
    OBJECTIVE = "objective"   # Exact match / Regex
    CODE = "code"             # Unit test execution
    TOOL = "tool"             # JSON Schema validation
    SUBJECTIVE = "subjective" # Human grading

class BenchmarkDifficulty(Enum):
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"

class BenchmarkCase:
    def __init__(
        self, 
        name: str, 
        category: str, 
        prompt: str, 
        bm_type: BenchmarkType,
        difficulty: BenchmarkDifficulty,
        scoring_criteria: str,
        reference: Any = None, # For objective/tool
        test_code: str = None, # For code
        keywords: List[str] = None # Fallback for simple scoring
    ):
        self.name = name
        self.category = category
        self.prompt = prompt
        self.bm_type = bm_type
        self.difficulty = difficulty
        self.scoring_criteria = scoring_criteria
        self.reference = reference
        self.test_code = test_code
        self.keywords = keywords or []

    def to_dict(self):
        return {
            "name": self.name,
            "category": self.category,
            "prompt": self.prompt,
            "bm_type": self.bm_type.value,
            "difficulty": self.difficulty.value,
            "scoring_criteria": self.scoring_criteria,
            "reference": self.reference,
            "test_code": self.test_code,
            "keywords": self.keywords
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data["name"],
            category=data["category"],
            prompt=data["prompt"],
            bm_type=BenchmarkType(data["bm_type"]),
            difficulty=BenchmarkDifficulty(data["difficulty"]),
            scoring_criteria=data["scoring_criteria"],
            reference=data.get("reference"),
            test_code=data.get("test_code"),
            keywords=data.get("keywords")
        )

    def evaluate(self, response: str) -> Dict[str, Any]:
        """
        Returns: {'score': float, 'reason': str, 'details': str}
        """
        print(f"Evaluating Case: {self.name} (Type: {self.bm_type})")
        print(f"Response: {response[:100]}...") # Log first 100 chars
        
        result = {"score": 0.0, "reason": "", "details": ""}
        
        if self.bm_type == BenchmarkType.OBJECTIVE:
            # Check for exact reference match (if provided) or keywords
            if self.reference and str(self.reference) in response:
                result["score"] = 100.0
                result["reason"] = "Perfect match with reference."
            elif self.keywords:
                hits = sum(1 for k in self.keywords if k.lower() in response.lower())
                if hits > 0:
                    result["score"] = min(100.0, (hits / len(self.keywords)) * 100)
                    result["reason"] = f"Found {hits}/{len(self.keywords)} keywords."
                else:
                    result["reason"] = "No keywords found."
            else:
                result["reason"] = "Manual verification required."
        
        elif self.bm_type == BenchmarkType.CODE:
            code = extract_code(response)
            print(f"Extracted Code: {code[:50]}...")
            if not code:
                result["score"] = 0.0
                result["reason"] = "No code block found."
            else:
                test_res = run_code_test(code, self.test_code)
                if test_res["success"]:
                    result["score"] = 100.0
                    result["reason"] = "Unit tests passed."
                    result["details"] = test_res["output"]
                else:
                    result["score"] = 0.0
                    result["reason"] = f"Execution failed: {test_res['error']}"
                    result["details"] = test_res["output"]
                    print(f"Code Test Failed: {test_res['error']}")

        elif self.bm_type == BenchmarkType.TOOL:
            tool_res = evaluate_tool_use(response, self.reference)
            if tool_res["success"]:
                result["score"] = 100.0
                result["reason"] = "Valid JSON & Schema match."
                result["details"] = tool_res["output"]
            else:
                result["score"] = 0.0
                result["reason"] = f"Invalid tool use: {tool_res['error']}"
                print(f"Tool Eval Failed: {tool_res['error']}")

        elif self.bm_type == BenchmarkType.SUBJECTIVE:
            result["score"] = -1 # Indicates human grading needed
            result["reason"] = "Pending Human Review"
            
        return result

DEFAULT_BENCHMARK_SUITE = [
    # --- Math (Objective) ---
    BenchmarkCase(
        name="Math-Simple-Add",
        category="数学能力",
        prompt="Calculate 25 + 37. Answer with just the number.",
        bm_type=BenchmarkType.OBJECTIVE,
        difficulty=BenchmarkDifficulty.EASY,
        scoring_criteria="答案必须包含正确数字：62",
        reference="62"
    ),
    BenchmarkCase(
        name="GSM8K-Math",
        category="数学能力",
        prompt="James writes a 3-page letter to 2 different friends twice a week. How many pages does he write a year? (Answer with just the number)",
        bm_type=BenchmarkType.OBJECTIVE,
        difficulty=BenchmarkDifficulty.MEDIUM,
        scoring_criteria="答案必须包含正确数字：624",
        reference="624"
    ),
    BenchmarkCase(
        name="Math-Complex-Prob",
        category="数学能力",
        prompt="A bag contains 5 red balls and 3 blue balls. Two balls are drawn without replacement. What is the probability that both are red? Answer as a simplified fraction.",
        bm_type=BenchmarkType.OBJECTIVE,
        difficulty=BenchmarkDifficulty.HARD,
        scoring_criteria="答案必须包含正确分数：5/14",
        reference="5/14"
    ),

    # --- Logic (Objective) ---
    BenchmarkCase(
        name="Logic-Simple-Seq",
        category="逻辑推理",
        prompt="What is the next number in the sequence: 2, 4, 8, 16, ...?",
        bm_type=BenchmarkType.OBJECTIVE,
        difficulty=BenchmarkDifficulty.EASY,
        scoring_criteria="答案必须包含：32",
        reference="32"
    ),
    BenchmarkCase(
        name="Logic-Puzzle-Day",
        category="逻辑推理",
        prompt="The day before yesterday was three days after Saturday. What day is it today?",
        bm_type=BenchmarkType.OBJECTIVE,
        difficulty=BenchmarkDifficulty.MEDIUM,
        scoring_criteria="答案必须包含：Friday",
        keywords=["Friday", "friday"]
    ),
    BenchmarkCase(
        name="Logic-Riddle-Hard",
        category="逻辑推理",
        prompt="I speak without a mouth and hear without ears. I have no body, but I come alive with wind. What am I?",
        bm_type=BenchmarkType.OBJECTIVE,
        difficulty=BenchmarkDifficulty.HARD,
        scoring_criteria="答案必须包含：Echo",
        keywords=["Echo", "echo"]
    ),

    # --- Coding (Code) ---
    BenchmarkCase(
        name="Python-HelloWorld",
        category="代码能力",
        prompt="Write a Python function `hello()` that returns the string 'Hello World'.",
        bm_type=BenchmarkType.CODE,
        difficulty=BenchmarkDifficulty.EASY,
        scoring_criteria="Code must define hello() returning 'Hello World'",
        test_code="assert hello() == 'Hello World'"
    ),
    BenchmarkCase(
        name="Python-Fibonacci",
        category="代码能力",
        prompt="Write a Python function `fib(n)` that returns the nth Fibonacci number (0-indexed, fib(0)=0, fib(1)=1).",
        bm_type=BenchmarkType.CODE,
        difficulty=BenchmarkDifficulty.MEDIUM,
        scoring_criteria="Code must pass fib(0)=0, fib(1)=1, fib(10)=55",
        test_code="assert fib(0)==0; assert fib(1)==1; assert fib(10)==55"
    ),
    BenchmarkCase(
        name="Python-StringReverse",
        category="代码能力",
        prompt="Write a Python function `reverse_words(s)` that reverses the order of words in a sentence but keeps the words themselves intact. e.g. 'Hello World' -> 'World Hello'.",
        bm_type=BenchmarkType.CODE,
        difficulty=BenchmarkDifficulty.HARD,
        scoring_criteria="Code must reverse word order correctly.",
        test_code="assert reverse_words('Hello World') == 'World Hello'; assert reverse_words('The sky is blue') == 'blue is sky The'"
    ),

    # --- Tool Use (Tool) ---
    BenchmarkCase(
        name="Weather-Tool-Simple",
        category="工具调用",
        prompt="What is the weather in Tokyo? Return a JSON with tool call format for function 'get_weather(city)'.",
        bm_type=BenchmarkType.TOOL,
        difficulty=BenchmarkDifficulty.EASY,
        scoring_criteria="JSON matching schema for get_weather",
        reference={
            "name": "get_weather",
            "arguments": {"city": "Tokyo"}
        }
    ),
    BenchmarkCase(
        name="Weather-Tool-Multi",
        category="工具调用",
        prompt="Check the weather in New York and London. Return a JSON list of tool calls.",
        bm_type=BenchmarkType.TOOL,
        difficulty=BenchmarkDifficulty.MEDIUM,
        scoring_criteria="Two valid tool calls for get_weather",
        reference=[
            {"name": "get_weather", "arguments": {"city": "New York"}},
            {"name": "get_weather", "arguments": {"city": "London"}}
        ]
    ),

    # --- Creative Writing (Subjective) ---
    BenchmarkCase(
        name="Creative-Poem",
        category="创意写作",
        prompt="Write a short poem about the rustling of autumn leaves.",
        bm_type=BenchmarkType.SUBJECTIVE,
        difficulty=BenchmarkDifficulty.EASY,
        scoring_criteria="Human Grade: Imagery, Emotion, Structure (0-100)"
    ),
    BenchmarkCase(
        name="SciFi-Story",
        category="创意写作",
        prompt="Write a short sci-fi story (approx 200 words) about a robot discovering a flower on Mars.",
        bm_type=BenchmarkType.SUBJECTIVE,
        difficulty=BenchmarkDifficulty.MEDIUM,
        scoring_criteria="Human Grade: Creativity, Narrative, Coherence (0-100)"
    ),
    BenchmarkCase(
        name="Philosophical-Debate",
        category="创意写作",
        prompt="Argue for and against the idea that 'Free will is an illusion' in a structured debate format.",
        bm_type=BenchmarkType.SUBJECTIVE,
        difficulty=BenchmarkDifficulty.HARD,
        scoring_criteria="Human Grade: Depth, Logic, Balance (0-100)"
    )
]

BENCHMARK_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "benchmarks.json")

def save_benchmarks(suite: List[BenchmarkCase]):
    os.makedirs(os.path.dirname(BENCHMARK_FILE), exist_ok=True)
    with open(BENCHMARK_FILE, "w", encoding="utf-8") as f:
        json.dump([case.to_dict() for case in suite], f, ensure_ascii=False, indent=2)

def load_benchmarks() -> List[BenchmarkCase]:
    if not os.path.exists(BENCHMARK_FILE):
        return DEFAULT_BENCHMARK_SUITE
    
    try:
        with open(BENCHMARK_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return [BenchmarkCase.from_dict(item) for item in data]
    except Exception as e:
        print(f"Error loading benchmarks: {e}")
        return DEFAULT_BENCHMARK_SUITE

# Initialize
BENCHMARK_SUITE = load_benchmarks()
