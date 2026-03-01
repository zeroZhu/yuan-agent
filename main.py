from re_act_agent import ReActAgent
from tools import list_files, read_file, rename_file
# agent = Agent(model, tools = [tools.list_files, tools.read_file, tools.rename_file], system_prompt = "你是一个文件管理助手")

# def main() -> None:
#     while True:
#         user_input = input("请输入你的指令: ")
#         response = agent.run_sync(user_input)
#         print(response)
def main() -> None:
    tools = [list_files, read_file, rename_file]
    agent = ReActAgent(model = "gemini-3-flash-preview", tools = tools)
    agent.run("列出所有文件")

if __name__ == "__main__":
    main()