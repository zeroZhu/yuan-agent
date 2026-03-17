
import os
from google import genai
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

print(os.getenv("DASHSCOPE_API_KEY"))
def main() -> None:
    model_kwargs = {"enable_thinking": False}
    llm = ChatOpenAI(
        model="qwen-max",
        api_key=os.getenv("DASHSCOPE_API_KEY") or "", # type: ignore
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

    res = llm.invoke("你好！请告诉我你是谁。")

    print(res.content)

if __name__ == "__main__":
    main()