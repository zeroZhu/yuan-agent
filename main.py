from langchain.agents import create_agent

def main() -> None:
    agent = create_agent(
        model="claude-sonnet-4-6",
        tools=[get_weather],
        system_prompt="You are a helpful assistant",
    )

    # Run the agent
    agent.invoke(
        {"messages": [{"role": "user", "content": "what is the weather in sf"}]}
    )

if __name__ == "__main__":
    main()