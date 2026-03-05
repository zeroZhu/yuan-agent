import os
import json
from google import genai
from dotenv import load_dotenv

load_dotenv()
print("GOOGLE_API_KEY:", os.getenv("GOOGLE_API_KEY"))

class pl_exe_agent:
    def __init__(self, model: str):
        self.model = model
        self.client = genai.Client()

    def plan_task(goal: str) -> str:
        """
        计划任务，根据任务描述，生成任务计划。
        :param task: 任务描述
        :return: 任务计划
        """
        prompt = f"""
        你是一个任务规划专家。请将用户的目标拆解为 3-5 个具体的、可执行的步骤。
        必须以 JSON 数组格式输出，例如：["步骤1", "步骤2"]。
        
        用户目标：{goal}
        """
 