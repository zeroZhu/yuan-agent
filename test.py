import re
import inspect
from tools import list_files, read_file, rename_file

def init_tool_list(self) -> None:
    tool_descriptions = []
    self.tool_list = [tool.__name__ for tool in self.tools]
    for func in self.tools.values():
        name = func.__name__
        signature = str(inspect.signature(func))
        doc = inspect.getdoc(func)
        tool_descriptions.append(f"- {name}{signature}: {doc}")
    return "\n".join(tool_descriptions)

def main() -> None:
    message = """<question>帮我找一个简单的番茄炒蛋食谱，并看看家里的冰箱里有没有西红柿。</question>
        <thought>这个任务分两步。第一步，找到番茄炒蛋的食谱。第二步，检查冰箱里是否有西红柿。我先用 find_recipe 工具找食谱。</thought>
        <action>find_recipe(dish="番茄炒蛋")</action>
        <observation>简单的番茄炒蛋食谱：将2个鸡蛋打散，2个番茄切块。热油，先炒鸡蛋，盛出。再热油，炒番茄至软烂，加入鸡蛋，放盐调味即可。</observation>
        <thought>好的，我已经有食谱了。食谱需要西红柿。现在我需要用 check_fridge 工具看看冰箱里有没有西红柿。</thought>
        <action>check_fridge(item="西红柿")</action>
        <observation>冰箱检查结果：有3个西红柿。</observation>
        <thought>我找到了食谱，并且确认了冰箱里有西红柿。可以回答问题了。</thought>
        <final_answer>简单的番茄炒蛋食谱是：鸡蛋打散，番茄切块。先炒鸡蛋，再炒番茄，混合后加盐调味。冰箱里有3个西红柿。</final_answer>"""
    thout_match = re.search(r"<thought>(.*?)</thought>", message, re.DOTALL)
    print(thout_match.group(0))

if __name__ == "__main__":
    main()