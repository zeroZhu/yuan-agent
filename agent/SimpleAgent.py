from typing import Optional, Any
from ..core import Agent, Config, Message

class SimpleAgent(Agent):
    def __init__(self, name: str, llm: Any, system_prompt: Optional[str] = None, config: Optional[Config] = None, tool_registry: Optional['ToolRegistry'] = None, enable_tool_calling: bool = True):
        super().__init__(name, llm, system_prompt, config)
        self.tool_registry = tool_registry
        self.enable_tool_calling = enable_tool_calling and tool_registry is not None
    
    def run(self, input: str, max_tool_calls: int = 3, **kwargs) -> list[Message]:
        """运行Agent，根据输入消息生成响应"""
        
        # 构建消息列表
        messages = []

        # 添加历史系统消息
        enhanced_system_prompt = self._get_enhanced_system_prompt()
        messages.append(Message(role="system", content=system_prompt))

        return super().run(messages)

    def _get_enhanced_system_prompt(self) -> str:
        """构建增强后的系统提示，包含工具信息"""
        base_prompt = self.system_prompt or "你是一个出色的AI助手，能够执行各种任务。你可以调用以下工具：{tool_names}"
        if not self.enable_tool_calling or not self.tool_registry:
            return base_prompt
        
        tools_description = self.tool_registry.get_tools_description()
        if not tools_description or tools_description == "暂无可用工具":
            return base_prompt
        
        tools_section = self.tool_registry.get_tools_selection()

        return base_prompt + tools_section