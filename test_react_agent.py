import os
from re_act_agent import ReActAgent

def test_function():
    """测试函数"""
    return "测试函数执行成功"

def main():
    # 创建 ReActAgent 实例model="qwen3.5-plus",
    agent = ReActAgent(
        model="qwen-max",  # 使用 OpenAI 的模型
        tools=[]
    )
    
    # 测试 agent
    try:
        result = agent.run("请帮我生成一套包含年龄、姓名、手机号的表单json返回给我")
        print(f"测试结果: {result}")
    except Exception as e:
        print(f"测试出错: {e}")

if __name__ == "__main__":
    main()
