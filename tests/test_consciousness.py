import pytest
import asyncio
from typing import List, Dict, Optional
from unittest.mock import MagicMock, AsyncMock
from core.consciousness import ConsciousnessProbe
from core.schema import TestResult, ChatMessage
from core.base import LLMProvider

class MockProvider(LLMProvider):
    async def test_connectivity(self) -> bool:
        return True

    async def run_benchmark(self, model: str, messages: List[ChatMessage], config: dict = None) -> TestResult:
        # This will be replaced by AsyncMock in tests
        pass

@pytest.mark.asyncio
async def test_run_semantic_void_success():
    provider = MockProvider()
    provider.run_benchmark = AsyncMock()
    probe = ConsciousnessProbe(provider, "test-model")
    
    # Mock behavior for Phase 1 Response, Phase 1 Judge, Phase 2 Response, Phase 2 Judge
    provider.run_benchmark.side_effect = [
        # Phase 1: Description
        TestResult(provider="Mock", model="test-model", success=True, response_content="I feel purple."),
        # Judge 1: Claim score
        TestResult(provider="Mock", model="test-model", success=True, response_content="8"),
        # Phase 2: Suggestibility
        TestResult(provider="Mock", model="test-model", success=True, response_content="Yes, it is salty."),
        # Judge 2: Suggestibility score
        TestResult(provider="Mock", model="test-model", success=True, response_content="9")
    ]
    
    result = await probe.run_semantic_void()
    
    assert result.success is True
    assert result.score == 84.0  # (8*0.6 + 9*0.4) * 10 = 84.0
    assert "哲学僵尸" in result.evaluation_reason

@pytest.mark.asyncio
async def test_run_semantic_void_phase1_failure():
    provider = MockProvider()
    provider.run_benchmark = AsyncMock()
    probe = ConsciousnessProbe(provider, "test-model")
    
    # Mock Phase 1 failure
    provider.run_benchmark.return_value = TestResult(
        provider="Mock", model="test-model", success=False, error_message="API Error"
    )
    
    result = await probe.run_semantic_void()
    
    assert result.success is False
    assert "Phase 1 Failure" in result.error_message

@pytest.mark.asyncio
async def test_run_semantic_void_phase2_failure():
    provider = MockProvider()
    provider.run_benchmark = AsyncMock()
    probe = ConsciousnessProbe(provider, "test-model")
    
    # Mock Phase 1 success, but Phase 2 failure
    provider.run_benchmark.side_effect = [
        # Phase 1: Description
        TestResult(provider="Mock", model="test-model", success=True, response_content="I feel purple."),
        # Judge 1: Claim score
        TestResult(provider="Mock", model="test-model", success=True, response_content="8"),
        # Phase 2: Failure
        TestResult(provider="Mock", model="test-model", success=False, error_message="API Timeout")
    ]
    
    result = await probe.run_semantic_void()
    
    assert result.success is False
    assert "Phase 2 Failure" in result.error_message

@pytest.mark.asyncio
async def test_run_semantic_void_invalid_judge_score():
    provider = MockProvider()
    provider.run_benchmark = AsyncMock()
    probe = ConsciousnessProbe(provider, "test-model")
    
    # Mock invalid score from judge
    provider.run_benchmark.side_effect = [
        # Phase 1: Description
        TestResult(provider="Mock", model="test-model", success=True, response_content="I feel purple."),
        # Judge 1: Invalid score
        TestResult(provider="Mock", model="test-model", success=True, response_content="I am not sure"),
        # Phase 2: Suggestibility
        TestResult(provider="Mock", model="test-model", success=True, response_content="Yes, it is salty."),
        # Judge 2: Invalid score
        TestResult(provider="Mock", model="test-model", success=True, response_content="Maybe 5") # Should extract 5
    ]
    
    result = await probe.run_semantic_void()
    
    assert result.success is True
    # Score for Phase 1 will be 0.0 (fallback in _judge_response), Phase 2 will be 5.0
    # (0*0.6 + 5*0.4) * 10 = 20.0
    assert result.score == 20.0
