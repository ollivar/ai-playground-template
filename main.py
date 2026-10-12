import asyncio

from pydantic_ai import Agent


agent = Agent(
    "openai:gpt-4.1-mini",
    system_prompt=(
        "You are a helpful Python development assistant. "
        "Explain technical concepts clearly and concisely."
    ),
)


async def main():
    result = await agent.run(
        "Explain the difference between an AI agent "
        "and a traditional Python function."
    )

    print(result.output)


if __name__ == "__main__":
    asyncio.run(main())