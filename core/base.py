from abc import ABC, abstractmethod
from typing import List
from .schema import TestResult, ChatMessage

class LLMProvider(ABC):
    @abstractmethod
    async def test_connectivity(self) -> bool:
        """测试基础连通性"""
        pass

    @abstractmethod
    async def run_benchmark(self, model: str, messages: List[ChatMessage]) -> TestResult:
        """运行完整的性能测试"""
        pass
