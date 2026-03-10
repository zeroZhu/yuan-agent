from google import genai
from tools import list_files, read_file, rename_file
import json

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

def main() -> None:
    ret = json.loads("[11111, 111111]")
    print(isinstance(ret, list))

if __name__ == "__main__":
    main()