from typing import Dict, Any, List
from pydantic import BaseModel
from abc import ABC, abstractmethod
from hello_agents import HelloAgentsLLM

class ToolParameter(BaseModel):
    """工具参数类"""
    name: str
    description: str
    required: bool = True
    default: Any = None


class Tool(ABC):
    """工具基类"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    def run(self, parameters: Dict[str, Any]) -> str:
        """执行工具"""
        pass

    @abstractmethod
    def get_parameters(self) -> List[ToolParameter]:
        """获取工具参数定义"""
        pass