# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "openai",
#     "requests",
#     "pydantic",
# ]
# ///

import json
import os
import requests

from openai import OpenAI
from pydantic import BaseModel, Field

# --------------------------------------------------------------
# Initialize OpenAI client
# --------------------------------------------------------------

client = OpenAI()

MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-nano")


# --------------------------------------------------------------
# Define our Python functions
# --------------------------------------------------------------


def search_kb(question: str):
    """
    Load the knowledge base from a JSON file.

    This is a mock retrieval function.
    It returns the entire knowledge base.
    """

    with open("kb.json", "r", encoding="utf-8") as f:
        return json.load(f)


def get_weather(latitude: float, longitude: float):
    """
    Get current weather for the specified coordinates.
    """

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,wind_speed_10m",
        "temperature_unit": "celsius",
    }

    response = requests.get(
        url,
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    return data["current"]


# --------------------------------------------------------------
# Define tools available to OpenAI
# --------------------------------------------------------------

tools = [
    {
        "type": "function",
        "function": {
            "name": "search_kb",
            "description": (
                "Search the e-commerce store knowledge base "
                "for information about policies, products, "
                "shipping, and returns."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The user's question",
                    }
                },
                "required": ["question"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": (
                "Get current weather for a location using latitude and longitude."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "latitude": {
                        "type": "number",
                        "description": "Latitude of the location",
                    },
                    "longitude": {
                        "type": "number",
                        "description": "Longitude of the location",
                    },
                },
                "required": ["latitude", "longitude"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
]


# --------------------------------------------------------------
# Execute the requested tool
# --------------------------------------------------------------


def call_function(name: str, args: dict):

    print(f"\n[TOOL SELECTED] {name}")
    print(f"[ARGUMENTS] {args}")

    if name == "search_kb":
        return search_kb(**args)

    elif name == "get_weather":
        return get_weather(**args)

    else:
        return {"error": f"Unknown tool: {name}"}


# --------------------------------------------------------------
# Define system instructions
# --------------------------------------------------------------

system_prompt = """
You are a helpful assistant.

You can answer questions about:
1. An e-commerce store using the search_kb tool.
2. Current weather using the get_weather tool.

Choose the appropriate tool based on the user's question.

For store questions, use search_kb.
For weather questions, use get_weather.

If a question requires both tools, you may use both.

Do not invent store policies or weather measurements.

The weather tool returns temperatures in celsius.

Be concise and helpful.
"""


# --------------------------------------------------------------
# Main chat function
# --------------------------------------------------------------


def chat(user_input: str, messages: list[dict]) -> str:

    # Add the user's question to conversation history.
    messages.append(
        {
            "role": "user",
            "content": user_input,
        }
    )

    # Limit the number of tool-calling rounds.
    max_tool_rounds = 5

    for round_number in range(max_tool_rounds + 1):
        print(f"\n[API CALL] Round {round_number + 1}")

        completion = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            max_completion_tokens=1000,
        )

        # Extract the assistant's message.
        assistant_message = completion.choices[0].message

        # Add the assistant's response to conversation history.
        messages.append(assistant_message.model_dump(exclude_none=True))

        # Check whether the model requested any tools.
        if not assistant_message.tool_calls:
            return assistant_message.content or ""

        # Stop before executing additional tools if limit reached.
        if round_number >= max_tool_rounds:
            return "Maximum tool rounds reached."

        # Execute every requested tool.
        for tool_call in assistant_message.tool_calls:
            name = tool_call.function.name

            try:
                args = json.loads(tool_call.function.arguments)

                if not isinstance(args, dict):
                    raise ValueError("Tool arguments must be a JSON object.")

                result = call_function(name, args)

                print(f"[TOOL RESULT] {result}")

            except Exception as e:
                print(f"[TOOL ERROR] {type(e).__name__}: {e}")
                result = {"error": str(e)}

            # Send the tool result back to OpenAI.
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result),
                }
            )

    return "Maximum tool rounds reached."


# --------------------------------------------------------------
# Interactive command-line interface
# --------------------------------------------------------------


def main():

    messages = [
        {
            "role": "developer",
            "content": system_prompt,
        }
    ]

    print("\nAI Assistant Started")
    print("Ask about store policies or current weather.")
    print("Type 'exit' to quit.\n")

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() in ("exit", "quit"):
            print("Goodbye!")
            break

        if not user_input:
            continue

        try:
            response = chat(user_input, messages)

            print(f"\nAssistant: {response}\n")

        except Exception as e:
            print(f"\nError: {e}\n")


if __name__ == "__main__":
    print("\nTesting weather API directly...")
    try:
        weather = get_weather(33.749, -84.388)
        print(weather)
    except Exception as e:
        print(f"Weather API error: {type(e).__name__}: {e}")
    main()
