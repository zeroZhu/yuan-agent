import os
import re
import ast
import inspect
import platform
from typing import Tuple, Callable, Literal, List
from string import Template
from google import genai
from google.genai import types
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from system_prompt_template import system_prompt_template

load_dotenv()
print("GOOGLE_API_KEY:", os.getenv("GOOGLE_API_KEY"))

class Feedback(BaseModel):
    sentiment: Literal["positive", "neutral", "negative"]
    summary: str

class ReActAgent:
    def __init__(self, model: str, tools: list[Callable]) -> None:
        self.model = model
        self.tools = { tool.__name__: tool for tool in tools }
        self.client = genai.Client()
        self.system_prompt = self.render_system_prompt()

    def run(self, prompt: str) -> None:
        history_messages = [
            types.Content(role="user", parts=[types.Part(text=f"<question>{prompt}</question>")]),
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
            history_messages.append(types.Content(role="user", parts=[types.Part(text=f"<observation>{observation}</observation>")]))
    
    def get_tool_list(self) -> str:
        tool_descriptions = []
        for name,func in self.tools.items():
            signature = str(inspect.signature(func))
            doc = inspect.getdoc(func) or "无描述"
            tool_descriptions.append(f"- {name}{signature}: {doc}")
        return "\n\n\n".join(tool_descriptions)

    def render_system_prompt(self) -> str:
        tool_list = self.get_tool_list()
        file_list = self.tools["list_files"]()
        file_list_str = str(file_list) if file_list else "无文件"
        return Template(system_prompt_template).substitute(
            operating_system=self.get_operating_system_name(),
            tool_list=tool_list,
            file_list=file_list_str
        )

    def call_model(self, contents) -> str:
        print("\n\n正在请求模型，请稍等...")
        # 启用流式响应
        # response_stream = self.client.models.generate_content_stream(
        #     model=self.model, 
        #     contents=prompt,
        #     config={
        #         "system_instruction": self.system_prompt,
        #     },
        # )
        # for chunk in response_stream:
        #     print(chunk.candidates[0].content.parts[0].text)
        response = self.client.models.generate_content(
            model=self.model, 
            contents=contents,
            config={
                "system_instruction": self.system_prompt,
            },
        )
        print(response.text)
        contents.append(types.Content(role="user", parts=[types.Part(text=response.text)]))
        print("\n\n模型返回完毕，开始解析...")
        return response.text if response.text else ""

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
