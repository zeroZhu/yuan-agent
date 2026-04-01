from typing import Any
from ..core import Agent, Config, Message
from ..tool import ToolRegistry

class SimpleAgent(Agent):
    def __init__(self, name: str, llm: Any, system_prompt: str | None = None, config: Config | None = None, tool_registry: ToolRegistry | None = None, enable_tool_calling: bool = True):
        super().__init__(name, llm, system_prompt, config)
        self.tool_registry = tool_registry
        self.enable_tool_calling = enable_tool_calling and tool_registry is not None
    
    def run(self, input: str, max_tool_calls: int = 3, **kwargs) -> Message:
        """运行Agent，根据输入消息生成响应"""
        
        # 构建消息列表
        messages = []

        # 添加系统消息
        enhanced_system_prompt = self._get_enhanced_system_prompt()
        messages.append(Message(role="system", content=enhanced_system_prompt))

        # 添加历史消息
        messages.append(Message(role="user", content=input))

        if not self.tool_registry:
            return self._run_without_tool(messages)

        return self._run_with_tool(messages)

    def _run_without_tool(self, messages: list[Message]) -> Message:
        """运行Agent，不包含工具调用"""
        res = self.llm.invoke
        return super().run(messages)

    def _run_with_tool(self, messages: list[Message]) -> Message:
        """运行Agent，包含工具调用"""
        return super().run(messages)

    def _get_enhanced_system_prompt(self) -> str:
        """构建增强后的系统提示，包含工具信息"""
        base_prompt = self.system_prompt or "你是一个出色的AI助手，能够执行各种任务。你可以调用以下工具：{tool_names}"
        if not self.enable_tool_calling or not self.tool_registry:
            return base_prompt
        
        tools_description = self.tool_registry.get_tools_description()
        if not tools_description or tools_description == "暂无可用工具":
            return base_prompt
        

        tools_section = f"""
            ## 你可以使用以下工具来帮助回答问题
                可用工具：
                {tools_description}
            ## 工具调用格式：
                例如：[TOOL_CALL:{tool_name}:{parameters}] 或
                工具调用结果会自动插入到对话中，然后你可以基于结果继续回答。
        """
        return base_prompt + tools_section

    def _parse_tool_call(self, text: str) -> str:
        """
        解析大语言模型的响应，提取工具调用信息。
        参数：
            response：大语言模型的原始响应字符串。
        返回：
            工具调用信息字符串，格式为 "[TOOL_CALL:{tool_name}:{parameters}]" 或 ""。
        """
        pattern = r'\[TOOL_CALL:([^:]+):([^\]]+)\]'
        matches = re.findall(pattern, text)

        tool_calls = []
        for tool_name, parameters in matches:
            tool_calls.append({
                'tool_name': tool_name.strip(),
                'parameters': parameters.strip(),
                'original': f'[TOOL_CALL:{tool_name}:{parameters}]'
            })
        
        return tool_calls
    
    def _extract_tool_call(self, tool_name: str, parameters: str) -> str:
        """
        从大语言模型的响应中提取工具调用信息。
        参数：
            response：大语言模型的原始响应字符串。
        返回：
            工具调用信息字符串，格式为 "[TOOL_CALL:{tool_name}:{parameters}]" 或 ""。
        """
        if not self.tool_registry:
            return f"❌ 错误:未配置工具注册表"
        
        try:
            parameters = json.loads(parameters)
            tool = self.tool_registry.get_tool(tool_name)
            if not tool:
                return f"❌ 错误:工具 {tool_name} 未注册"
            result = tool.run(parameters)
            return f"✅ 工具{tool_name}调用成功:{result}"
        except Exception as e:
            return f"❌ 工具调用失败:{str(e)}"

    

