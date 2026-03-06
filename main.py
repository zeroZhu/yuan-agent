from re_act_agent import ReActAgent
from pl_exe_agent import PlExeAgent
from tools import list_files, read_file, rename_file
# agent = Agent(model, tools = [tools.list_files, tools.read_file, tools.rename_file], system_prompt = "你是一个文件管理助手")

# def main() -> None:
#     while True:
#         user_input = input("请输入你的指令: ")
#         response = agent.run_sync(user_input)
#         print(response)
def main() -> None:
    tools = [list_files, read_file, rename_file]
    # agent = ReActAgent(model = "gemini-2.5-flash", tools = tools)
    agent = PlExeAgent(model = "gemini-2.5-flash", tools = tools)
    while True:
        input_str = input('请输入你的指令: ')
        output_str = agent.run(input_str)
        print(f'模型返回结果： {output_str}')

if __name__ == "__main__":
    main()