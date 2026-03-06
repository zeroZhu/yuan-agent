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

    def run(self, prompt: str) -> str:
        """
        运行任务，根据用户输入，生成任务计划并执行任务。
        :param prompt: 用户输入
        :return: 任务执行结果
        """
        print(f"🚀 开始规划目标: {prompt}")
        # 1. 制定计划
        todo_list = self.plan_task(prompt)
        print(f"📋 计划已生成: {todo_list}")

        while len(todo_list) > 0:
            task = todo_list.pop(0)
            
            task_result = self.execute_task(task)
            print(f"✅ 任务执行完成: {task_result}")
        task_result = self.execute_task(task_plan)
        return task_result

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
        response = self.client.generate_content(prompt)
        return response.text

    def execute_task(self, task: str) -> str:
        """
        执行任务，根据任务计划，执行任务。
        :param task: 任务计划
        :return: 任务执行结果
        """
        prompt = f"""
        你是一个任务执行专家。请根据用户的任务计划，执行任务。
        必须以 JSON 格式输出，例如：{{"任务": "步骤1", "结果": "成功"}}。
        
        用户任务计划：{task}
        """
        print(f"🔧 开始执行任务: {task}")

        
    
 