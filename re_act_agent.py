import os
import re
import ast
import json
import inspect
import platform
from typing import Tuple, Callable, Literal, List
from string import Template
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from system_prompt_template import system_prompt_template

load_dotenv()

class Feedback(BaseModel):
    sentiment: Literal["positive", "neutral", "negative"]
    summary: str

class ReActAgent:
    def __init__(self, model: str, tools: list[Callable]) -> None:
        self.model = model
        self.tools = { tool.__name__: tool for tool in tools }
        self.client = OpenAI(            # 如果没有配置环境变量，请用阿里云百炼API Key替换：api_key="sk-xxx"
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        self.system_prompt = self.render_system_prompt()

    def run(self, prompt: str) -> None:
        history_messages = [
            {"role": "user", "content": f"<question>{prompt}</question>"}
        ]
        while True:
            # 请求模型
            content = self.call_model(history_messages)

            
            # 检测 Thought
            thought_match = re.search(r"<thought>(.*?)</thought>", content, re.DOTALL)
            if thought_match:
                thought = thought_match.group(1)
                print(f"\n\n💭 Thought: {thought}")

            # 检测 Final Answer
            if "<final_answer>" in content:
                final_answer = re.search(r"<final_answer>(.*?)</final_answer>", content, re.DOTALL)
                return final_answer.group(1)

            # 检测 Action
            action_match = re.search(r"<action>(.*?)</action>", content, re.DOTALL)
            if not action_match:
                raise RuntimeError("模型未输出 <action>")
            action = action_match.group(1)
            tool_name, args = self.parse_action(action)
            print(f"\n\n🔧 Action: {tool_name}({', '.join(args)})")

            try:
                observation = self.tools[tool_name](*args)
            except Exception as e:
                observation = f"工具执行错误：{str(e)}"
            print(f"\n\n🔍 Observation：{observation}")
            history_messages.append({"role": "user", "content": f"<observation>{observation}</observation>"})
    
    def get_tool_list(self) -> str:
        tool_descriptions = []
        for name,func in self.tools.items():
            signature = str(inspect.signature(func))
            doc = inspect.getdoc(func) or "无描述"
            tool_descriptions.append(f"- {name}{signature}: {doc}")
        return "\n\n\n".join(tool_descriptions)

    def render_system_prompt(self) -> str:
        tool_list = self.get_tool_list()
        file_list_str = "无文件"
        if "list_files" in self.tools:
            file_list = self.tools["list_files"]()
            file_list_str = str(file_list) if file_list else "无文件"
        return Template(system_prompt_template).substitute(
            operating_system=self.get_operating_system_name(),
            tool_list=tool_list,
            file_list=file_list_str
        )

    def render_form(self, title: str, schemas: list[dict]) -> str:
        return f"请根据以下字段渲染表单：{title}\n{schemas}"

    def call_model(self, contents) -> str:
        print("\n\n正在请求模型，请稍等...")
        # 构建完整的消息列表，包含系统提示
        messages = [
            {"role": "system", "content": self.system_prompt}
        ] + contents
        print("messages:", messages)
        # 调用 OpenAI API
        tools = [
            {
            "type": "function",
            "function": {
                "name": "render_form",
                "description": "当AI模型不清楚用户意图时，调用此函数渲染表单向用户提问",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "要渲染的表单标题"
                        },
                        "schemas": {
                            "type": "array",
                            "description": "要渲染的表单字段列表",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "field": {
                                        "type": "string",
                                        "description": "要渲染的表单字段名称"
                                    },
                                    "label": {
                                        "type": "string",
                                        "description": "要渲染的表单字段标签"
                                    },
                                    "component": {
                                        "type": "string",
                                        "description": "要渲染的表单组件名称, 可选值为: input, radio, checkbox"
                                    },
                                    "options": {
                                        "type": "array",
                                        "description": "如果组件为radio或checkbox，必须提供选项列表",
                                        "items": {
                                            "type": "string",
                                            "description": "选项值"
                                        }
                                    }
                                },
                                "required": ["field", "label", "component"],
                                "additionalProperties": False
                            }
                        }
                    },
                    "required": ["field", "label", "component"],
                    "additionalProperties": False
                }
            }
            }
        ]
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            tools=tools,
            tool_choice="auto"
        )
        
        print(response)
        assistant_message = response.choices[0].message
        messages.append(assistant_message)
        if assistant_message.tool_calls:
            # 模型决定调用函数
            for tool_call in assistant_message.tool_calls:
                func_name = tool_call.function.name
                func_args = json.loads(tool_call.function.arguments)
                
                print(f"🤖 模型请求调用函数: {func_name}, 参数: {func_args}")
                
                # 执行实际函数
                if func_name == "render_form":
                    result = render_form(**func_args)
                    
                    # 将执行结果反馈给模型
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result
                    })

            # 6. 第二轮对话：带结果再次请求模型生成最终回答
            final_response = client.chat.completions.create(
                model="qwen-plus",
                messages=messages,
                tools=tools
            )
            
            print("✅ 最终回答:", final_response.choices[0].message.content)
        else:
            print("💬 普通回答:", assistant_message.content)
        # 获取响应内容
        response_text = response.output_text
        print(response_text)
        contents.append({"role": "assistant", "content": response_text})
        print("\n\n模型返回完毕，开始解析...")
        return response_text if response_text else ""

    def get_operating_system_name(self):
        os_map = {
            "Darwin": "macOS",
            "Windows": "Windows",
            "Linux": "Linux"
        }

        return os_map.get(platform.system(), "Unknown")

    def parse_action(self, code_str: str) -> Tuple[str, List[str]]:
        match = re.match(r'(\w+)\((.*)\)', code_str, re.DOTALL)
        if not match:
            raise ValueError("Invalid function call syntax")

        func_name = match.group(1)
        args_str = match.group(2).strip()

        # 手动解析参数，特别处理包含多行内容的字符串
        args = []
        current_arg = ""
        in_string = False
        string_char = None
        i = 0
        paren_depth = 0
        
        while i < len(args_str):
            char = args_str[i]
            
            if not in_string:
                if char in ['"', "'"]:
                    in_string = True
                    string_char = char
                    current_arg += char
                elif char == '(':
                    paren_depth += 1
                    current_arg += char
                elif char == ')':
                    paren_depth -= 1
                    current_arg += char
                elif char == ',' and paren_depth == 0:
                    # 遇到顶层逗号，结束当前参数
                    args.append(self._parse_single_arg(current_arg.strip()))
                    current_arg = ""
                else:
                    current_arg += char
            else:
                current_arg += char
                if char == string_char and (i == 0 or args_str[i-1] != '\\'):
                    in_string = False
                    string_char = None
            
            i += 1
        
        # 添加最后一个参数
        if current_arg.strip():
            args.append(self._parse_single_arg(current_arg.strip()))
        
        return func_name, args
    def _parse_single_arg(self, arg_str: str):
        """解析单个参数"""
        arg_str = arg_str.strip()
        
        # 如果是字符串字面量
        if (arg_str.startswith('"') and arg_str.endswith('"')) or \
           (arg_str.startswith("'") and arg_str.endswith("'")):
            # 移除外层引号并处理转义字符
            inner_str = arg_str[1:-1]
            # 处理常见的转义字符
            inner_str = inner_str.replace('\\"', '"').replace("\\'", "'")
            inner_str = inner_str.replace('\\n', '\n').replace('\\t', '\t')
            inner_str = inner_str.replace('\\r', '\r').replace('\\\\', '\\')
            return inner_str
        
        # 尝试使用 ast.literal_eval 解析其他类型
        try:
            return ast.literal_eval(arg_str)
        except (SyntaxError, ValueError):
            # 如果解析失败，返回原始字符串
            return arg_str
