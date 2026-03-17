from dotenv import load_dotenv
from browser_use import Agent, ChatGoogle

# Read GOOGLE_API_KEY into env
load_dotenv()

class BrowserUseAgent(Agent):
    def __init__(self):
        self.llm = ChatGoogle(model='gemini-3-flash-preview')

    def run(self, task: str) -> str:
        self.agent = Agent(task=task, llm=self.llm)
        return self.agent.run()