import os
import re
import inspect
import platform
from typing import Callable, Literal
from string import Template
from google import genai
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
        print('system_prompt', self.system_prompt)

    def run(self, prompt: str) -> None:
        # while True:
        #     # 请求模型
        #     content = self.call_model(f"<question>{prompt}</question>")

        #     # 检测 Thought
        #     thought_match = re.search(r"<thought>(.*?)</thought>", content, re.DOTALL)
        #     if thought_match:
        #         thought = thought_match.group(1)
        #         print(f"\n\n💭 Thought: {thought}")

        #     # 检测 Final Answer
        #     if "<final_answer>" in content:
        #         final_answer = re.search(r"<final_answer>(.*?)</final_answer>", content, re.DOTALL)
        #         return final_answer.group(1)

        #     # 检测 Action
        #     action_match = re.search(r"<action>(.*?)</action>", content, re.DOTALL)
        #     if not action_match:
        #         raise RuntimeError("模型未输出 <action>")
        #     action = action_match.group(1)
        #     tool_name, args = self.parse_action(action)
        #     print(f"\n\n🔧 Action: {tool_name}({', '.join(args)})")
        self.call_model(f"<question>{prompt}</question>")
    
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
        response = []
        # 启用流式响应
        # response_stream = self.client.models.generate_content_stream(
        #     model=self.model, 
        #     contents=prompt,
        #     config={
        #         "response_mime_type": "application/json",
        #         "response_json_schema": Feedback.model_json_schema(),
        #     },
        # )
        # for chunk in response_stream:
        #     print(chunk.candidates[0].content.parts[0].text)
        response = self.client.models.generate_content(
            model=self.model, 
            contents=prompt
        )
        print(response.text())

    def get_operating_system_name(self):
        os_map = {
            "Darwin": "macOS",
            "Windows": "Windows",
            "Linux": "Linux"
        }

        return os_map.get(platform.system(), "Unknown")
