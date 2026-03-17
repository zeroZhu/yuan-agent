import os
from typing import List, Dict, Union
from dotenv import load_dotenv
from openai import OpenAI
# 加载 .env 文件中的环境变量
load_dotenv()

class llm:
  def __init__(self, model: str = "", api_key: str = "", base_url: str = "", timeout: int = 30):
    """
      初始化客户端。优先使用传入参数，如果未提供，则从环境变量加载。
    """
    self.model = model or os.getenv("DASHSCOPE_API_KEY")
    self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
    self.base_url = base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1"
    self.timeout = timeout
    
    if (not all([self.model, api_key, base_url])):
      raise ValueError("model, api_key, base_url must be provided")

    self.client = OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=self.timeout)
    
  
  def think(self, messages: List[Dict[str, str]], temperature: float = 0) -> str:
    """
      调用大语言模型进行思考，并返回其响应。
      参数：
        messages：包含用户消息和助手消息的列表，每个元素为一个字典，格式为 {"role": "user" | "assistant", "content": "消息内容"}。
        temperature：温度参数，用于控制生成的文本的随机性。默认值为0.5。
    """
    print(f"🧠 正在调用 {self.model} 模型...")
    try:
      response = self.client.responses.create(model=self.model, stream=True, input=messages) # type: ignore
      # 处理流式响应
      print("✅ 大语言模型响应成功:")
      collected_content = []
      for chunk in response:
          print(chunk)
          content = chunk.choices[0].delta.content or ""
          print(content, end="", flush=True)
          collected_content.append(content)
      return "".join(collected_content)
    except Exception as e:
      print(f"调用模型 {self.model} 时出错: {e}")
      raise e
   
