import asyncio
from browser_use_agent import BrowserUseAgent

async def main() -> None:
    browser_use_agent = BrowserUseAgent()
    response = await browser_use_agent.run("Find the number 1 post on Show HN")
    print(response)

if __name__ == "__main__":
    asyncio.run(main())