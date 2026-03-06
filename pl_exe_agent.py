import os
import json
from google import genai
from dotenv import load_dotenv

load_dotenv()
print("GOOGLE_API_KEY:", os.getenv("GOOGLE_API_KEY"))

class PlExeAgent:
    def __init__(self, model: str):
        self.model = model
        self.client = genai.Client()

    def run(self, prompt: str) -> None:
        """
        运行任务，根据用户输入，生成任务计划并执行任务。
        :param prompt: 用户输入
        :return: 任务执行结果
        """
        # 1. 制定计划
        todo_list = self.plan_task(prompt)

        # while len(todo_list) > 0:
        #     task = todo_list.pop(0)
        #     task_result = self.execute_task(task)


        # task_result = self.execute_task(task_plan)
        # return task_result

    def plan_task(self, prompt: str) -> list:
        """
        计划任务，根据用户需求，生成任务计划。
        :param prompt: 用户需求
        :return: 任务计划
        """
        system_prompt = f"""
        你是一个任务规划专家。请将用户的目标拆解为 3-5 个具体的、可执行的步骤。
        必须以 JSON 数组格式输出，例如：["步骤1", "步骤2"]。
        """

        print(f"🚀 开始规划目标: {prompt}")
        response = self.client.models.generate_content(
            model = self.model,
            contents=prompt,
            config={
                "system_instruction": system_prompt,
                "response_mime_type": "application/json",
            }
        )
        print(f"📋 计划已生成: {response.text}")
        return response.text

    def re_plan_task(self, goal: str, todo_list: list, result: str) -> list:
        """
        计划任务，根据任务描述，生成任务计划。
        :param task: 任务描述
        :return: 任务计划
        """
        prompt = f"""
        你是一个任务规划专家。主要任务是根据用户的目标、上次任务执行结果以及用户任务计划，重新规划任务计划。
        必须以 JSON 数组格式输出，例如：["步骤1", "步骤2"]。
        
        用户目标：{goal}
        用户任务计划：{todo_list}
        用户任务新计划：{todo_list}
        上次任务执行结果：{result}
        """


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

        print(f"✅ 任务执行完成: {task_result}")
        return result
        
    
 