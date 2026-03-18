from typing import Optional, Dict, Any
from abc import ABC, abstractmethod
from .config import Config
from .message import Message
from typing import List

class Agent(ABC):
    """智能体基类"""

    def __init__(self, name: str, description: str, system_prompt: str, llm: Any, config: Optional[Config]):
        self.name = name
        self.description = description
        self.system_prompt = system_prompt
        self.llm = llm
        self.config = config or Config()
        self._history: list[Message] = []

    @abstractmethod
    def run(self, input: str,  **other_params) -> Message:
        """执行智能体"""
        pass

    def add_message(self, message: Message):
        """添加消息到历史记录"""
        self._history.append(message)

    def clear_history(self):
        """清空智能体历史记录"""
        self._history.clear()

    def get_history(self) -> list[Message]:
        """获取智能体历史记录"""
        return self._history.copy()
        