import os
from dotenv import load_dotenv
from re_act_agent import ReActAgent
from tools import search_real_estate_price

load_dotenv()

def main():
    agent = ReActAgent(
        model="gemini-2.0-flash",
        tools=[search_real_estate_price]
    )
    
    result = agent.run("北京现在的房价是多少？")
    print("\n\n" + "="*50)
    print("最终答案：")
    print(result)

if __name__ == "__main__":
    main()
