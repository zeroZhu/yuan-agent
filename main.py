from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest
from langchain_google_genai import GoogleGenerativeAI

load_dotenv()
print("GOOGLE_API_KEY:", os.getenv("GOOGLE_API_KEY"))

base_model = GoogleGenerativeAI(model="gemini-2.5-flash")
advanced_model = GoogleGenerativeAI(model="gemini-3.1-pro-ultra-preview")

@middleware
def log_agent(model: str, prompt: str, response: str) -> None:
    print(f"Model: {model}")
    print(f"Prompt: {prompt}")
    print(f"Response: {response}")
    print("\n")

def main() -> None:
    agent = create_agent(
        model= baseModel,
        tools=[get_weather],
        system_prompt="You are a helpful assistant",
    )

    # Run the agent
    agent.invoke(
        {"messages": [{"role": "user", "content": "what is the weather in sf"}]}
    )

if __name__ == "__main__":
    main()