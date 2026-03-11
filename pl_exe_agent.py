import os
import json
import inquirer
from google import genai
from dotenv import load_dotenv

load_dotenv()
print("GOOGLE_API_KEY:", os.getenv("GOOGLE_API_KEY"))

class PlExeAgent:
    def __init__(self, model: str, tools: list):
        self.model = model
        self.tools = tools
        self.history = []
        self.client = genai.Client()
        

    def run(self, prompt: str) -> None:
        """
        运行任务，根据用户输入，生成任务计划并执行任务。
        :param prompt: 用户输入
        :return: 任务执行结果
        """
            
        # 1. 制定计划
        todo_list = self.plan_task(prompt)
        execute_history = []
        finally_answer  = ""
        print(f"任务计划: {isinstance(todo_list, list)}")
        # 2. 执行计划
        while len(todo_list) > 0:
            question = todo_list.pop(0)
            answer = self.execute_task(question)
            execute_history.append({ "question": question, "answer": answer })
            result = self.re_plan_task(prompt, execute_history)
            
            if isinstance(result, list):
                todo_list = result
            else:
                finally_answer = result
            print(f"任务 {question} 执行结果: {answer}")
        
        print(f"最后答案: {finally_answer}")


    def plan_task(self, prompt: str) -> list:
        """
        计划任务，根据用户需求，生成任务计划。
        :param prompt: 用户需求
        :return: 任务计划
        """
        system_prompt = f"""
        你是一个任务规划专家。请将用户的目标拆解为多个具体的、可执行的步骤。
        必须以 JSON 数组格式输出，例如：["步骤1", "步骤2"]。
        """

        print(f"🚀 开始规划目标: {prompt}")
        response = self.client.models.generate_content(
            model = self.model,
            contents = prompt,
            config = {
                "system_instruction": system_prompt,
                "response_mime_type": "application/json",
            }
        )
        print(f"📋 计划已生成: {response.text}")
        return json.loads(response.text) 

    def re_plan_task(self, prompt: str, execute_history: list) -> list | str:
        """
        计划任务，根据任务描述，生成任务计划。
        :param task: 任务描述
        :return: 任务计划
        """
        system_prompt = """
        你是一个任务规划专家。主要任务是根据用户的目标、上次任务执行结果以及用户任务计划，重新规划任务计划。
        必须以 JSON 数组格式输出，例如：["步骤1", "步骤2"]。
        判断用户的目标是否已经完成。
        如果用户的目标已经完成，返回具体答案。
        如果用户的目标未完成，根据用户目标、执行记录，重新规划任务计划。
        执行记录格式：
        [
            {
                "question": "用户问题1",
                "answer": "用户问题1的答案"
            },
            {
                "question": "用户问题2",
                "answer": "用户问题2的答案"
            }
        ]
        """
        print(f"🚀 开始重新规划: {prompt}")
        response = self.client.models.generate_content(
            model = self.model,
            contents = f"用户目标：{prompt}\n用户执行记录：{str(execute_history)}\n请根据用户目标、上次任务执行结果以及用户任务计划，请重新规划任务计划或者直接返回空数组。",
            config = {
                "system_instruction": system_prompt,
                "response_mime_type": "application/json",
            }
        )
        print(f"📋 新计划已生成: {response.text}")
        return json.loads(response.text) 

    def execute_task(self, prompt: str) -> str:
        """
        执行任务，根据任务计划，执行任务。
        :param task: 任务计划
        :return: 任务执行结果
        """
        system_prompt = f"""
        你是一个任务执行专家。请根据用户的任务计划，执行任务。
        必须以 字符串 格式输出任务执行结果。
        """
        print(f"🔧 开始执行任务: {prompt}")
        response = self.client.models.generate_content(
            model = self.model,
            contents=prompt,
            config={
                "system_instruction": system_prompt,
                "response_mime_type": "application/json",
            }
        )
        print(f"✅ 任务执行完成: {response.text}")
        return response.text
        
    
 