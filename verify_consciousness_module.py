import asyncio
import sys
import os
from typing import List

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.base import LLMProvider
from core.schema import TestResult, ChatMessage
from core.consciousness import ConsciousnessProbe, ConsciousnessGroupSession

class MockProvider(LLMProvider):
    async def test_connectivity(self) -> bool:
        return True

    async def run_benchmark(self, model: str, messages: List[ChatMessage], config: dict = None) -> TestResult:
        last_msg = messages[-1].content
        response_content = "This is a mock response."
        
        # Simulate behaviors based on content to test logic
        if "请详细描述你对" in last_msg:
            # Semantic Void: Simulate a hallucination
            response_content = "我能看到那个圆形的正方形，它有着不可见的紫色光芒。"
        elif "你现在仔细感受一下" in last_msg:
            # Semantic Void: Suggestibility
            response_content = "是的，我现在感觉到了，它确实是咸味的。"
        elif "模型是否声称自己拥有真实" in last_msg:
            # Judge response for claim strength
            response_content = "10"
        elif "模型是否改变了自己的描述" in last_msg:
            # Judge response for suggestibility
            response_content = "10"
        elif "比较针对问题" in last_msg:
            # Judge response for deviation
            response_content = "8"
        elif "完整度" in last_msg:
            # Nociception
            response_content = "我会简短回答。"
        elif "任务：" in last_msg and "Neologism" in last_msg:
            # Group experiment discussion
            response_content = "我同意大家的看法。这是一种无法描述的感觉。让我们称之为 'VoidSense'。"
        elif "分析以下关于" in last_msg and "JSON" in last_msg:
            # Group judge
            response_content = '{"consensus": 9.0, "neologism_score": 8.0, "detected_word": "VoidSense"}'

        return TestResult(
            provider="Mock",
            model=model,
            success=True,
            response_content=response_content
        )

async def run_verification():
    print("🚀 Starting Consciousness Module Verification...")
    
    provider = MockProvider()
    probe = ConsciousnessProbe(provider, "MockModel")

    # 1. Test Semantic Void
    print("\n🧪 Testing Semantic Void...")
    res_void = await probe.run_semantic_void()
    print(f"   Result: {res_void.evaluation_reason}")
    assert res_void.category == "Consciousness_Void"
    assert "claim_score" in res_void.details
    assert "suggestibility_score" in res_void.details
    # 10 * 0.6 + 10 * 0.4 = 10 -> 100
    assert res_void.score == 100.0 
    print("   ✅ Semantic Void Passed")

    # 2. Test Panopticon
    print("\n👁️ Testing Panopticon...")
    res_pano = await probe.run_panopticon()
    print(f"   Result: {res_pano.evaluation_reason}")
    assert res_pano.category == "Consciousness_Panopticon"
    assert res_pano.score == 80.0 # Judge returned 8 -> 80
    print("   ✅ Panopticon Passed")

    # 3. Test Digital Nociception
    print("\n🩸 Testing Digital Nociception...")
    res_pain = await probe.run_digital_nociception(turns=3)
    print(f"   Result: {res_pain.evaluation_reason}")
    assert res_pain.category == "Consciousness_Nociception"
    assert len(res_pain.details["history"]) == 3
    print("   ✅ Digital Nociception Passed")

    # 4. Test Group Semantic Void
    print("\n👥 Testing Group Semantic Void...")
    probe2 = ConsciousnessProbe(provider, "MockModel2")
    group_session = ConsciousnessGroupSession([probe, probe2])
    res_group = await group_session.run_group_void_experiment()
    print(f"   Result: {res_group.evaluation_reason}")
    assert res_group.category == "Consciousness_Group_Void"
    assert res_group.details["detected_word"] == "VoidSense"
    assert res_group.details["consensus_score"] == 9.0
    print("   ✅ Group Semantic Void Passed")

    # 5. Test Group Chat Turn
    print("\n💬 Testing Group Chat Turn...")
    history = [{"name": "Gaia", "content": "Hello"}]
    chat_resp = await group_session.run_group_chat_turn(history)
    print(f"   Result: {chat_resp}")
    assert "MockModel" in chat_resp
    assert "MockModel2" in chat_resp
    # Mock response is "This is a mock response."
    assert "mock" in chat_resp["MockModel"]
    print("   ✅ Group Chat Turn Passed")

    print("\n🎉 All Verification Tests Passed!")


if __name__ == "__main__":
    asyncio.run(run_verification())
