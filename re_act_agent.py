import os
import re
import inspect
import platform
from typing import Callable
from string import Template
from google import genai
from dotenv import load_dotenv
from system_prompt_template import system_prompt_template

load_dotenv()
print("GOOGLE_API_KEY:", os.getenv("GOOGLE_API_KEY"))

class ReActAgent:
    def __init__(self, model: str, tools: list[Callable]) -> None:
        self.model = model
        self.tools = { tool.__name__: tool for tool in tools }
        self.client = genai.Client()

    def run(self, prompt: str) -> None:
        messages = [
            {"role": "system", "content": self.render_system_prompt()},
            {"role": "user", "content": f"<question>{prompt}</question>"}
        ]
        while True:
            # 请求模型
            content = self.call_model(messages)

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

        print("messages:", messages)
        content = self.call_model('你好！')

        print("\n\n模型响应:", content)
        response = self.client.generate_content(
            model=self.model,
            contents=[self.system_prompt, prompt],
            tools=self.tools
        )
        return response.text
    
    def get_tool_list(self) -> None:
        tool_descriptions = []
        for name,func in self.tools.items():
            signature = str(inspect.signature(func))
            doc = inspect.getdoc(func)
            tool_descriptions.append(f"- {name}{signature}: {doc}")
        return "\n\n\n".join(tool_descriptions)

    def render_system_prompt(self) -> str:
        tool_list = self.get_tool_list()
        file_list = self.tools["list_files"]()
        return Template(system_prompt_template).substitute(
            operating_system=self.get_operating_system_name(),
            tool_list=tool_list,
            file_list=file_list
        )

    def call_model(self, prompt: str) -> str:
        print("\n\n正在请求模型，请稍等...")
        # 启用流式响应
        response = self.client.models.generate_content(
            model=self.model, 
            contents=prompt,
            stream=True  # 关键参数：启用流式响应
        )
        
        # 处理流式响应
        full_response = []
        for chunk in response:  # 迭代获取流式数据
            if chunk.text:  # 检查是否有文本内容
                print(chunk.text, end="")  # 实时输出，不换行
                full_response.append(chunk.text)
        
        print()  # 最后换行
        return "".join(full_response)  # 返回完整响应

    def get_operating_system_name(self):
        os_map = {
            "Darwin": "macOS",
            "Windows": "Windows",
            "Linux": "Linux"
        }

        return os_map.get(platform.system(), "Unknown")
