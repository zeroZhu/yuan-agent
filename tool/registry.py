from typing import Callable
from base import Tool, ToolParameter

class ToolRegistry:
    """工具注册类"""
    def __init__(self):
        self._tools: dict[str, Tool] = {}
        self._functions: dict[str, Tool] = {}

    def register_tool(self, tool: Tool):
        """注册工具"""
        if tool.name in self._tools:
            raise ValueError(f"⚠️工具 {tool.name} 已注册")
        self._tools[tool.name] = tool
        print(f"✅工具 {tool.name} 已注册")
    
    def unregister_tool(self, name: str):
        """注销工具"""
        if name not in self._tools:
            raise ValueError(f"⚠️工具 {name} 未注册")
        del self._tools[name]
        print(f"✅工具 {name} 已注销")
    
    def register_function(self, name: str, description: str, func: Callable[[str], str]):
        """
        直接注册函数作为工具（简便方式）

        Args:
            name: 工具名称
            description: 工具描述
            func: 工具函数，接受字符串参数，返回字符串结果
        """
        if name in self._functions:
            raise ValueError(f"⚠️函数 {name} 已注册")
        self._functions[name] = {
            "description": description,
            "func": func
        }
        print(f"✅函数 {name} 已注册")

    def unregister_function(self, name: str):
        """注销函数"""
        if name not in self._functions:
            raise ValueError(f"⚠️函数 {name} 未注册")
        del self._functions[name]
        print(f"✅函数 {name} 已注销")

    def clear(self):
        """清空所有注册的工具和函数"""
        self._tools.clear()
        self._functions.clear()
        print("✅所有工具和函数已注销")

    def get_tools_definitions(self) -> List[Dict[str, Any]]:
        """获取所有可用工具的格式化描述字符串"""
        descriptions = []
        for tool in self._tools.values():
          descriptions.append(f"""- {tool.name}: {tool.description}""")
        
        for key, item in self._functions.values():
          descriptions.append(f"""- {key}: {item.description}""")

        return "\n".join(descriptions) if descriptions else "暂无可用工具"
    
    def to_openai_schema(self) -> List[Dict[str, Any]]:
        """转换为 OpenAI function calling schema 格式

        用于 FunctionCallAgent，使工具能够被 OpenAI 原生 function calling 使用

        Returns:
            符合 OpenAI function calling 标准的 schema
        """
        parameters = self.get_parameters()


        for tool in self._tools.values():
            schemas.append({
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.get_parameters()
            })
        for key, item in self._functions.values():
            schemas.append({
                "name": key,
                "description": item.description,
                "parameters": item.get_parameters()
            })
        return schemas