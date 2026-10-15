# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "openai",
#     "pydantic",
# ]
# ///

import os
import sys
from typing import Any

from openai import OpenAI
from pydantic import BaseModel


# Specify the model for our tools - a tool is a function that the AI Agent can call to perform a specific task
# This is a standardized way to define the interface for tools that the AI Agent can use
class Tool(BaseModel):
    name: str
    description: str
    input_schema: dict[str, Any]


# Specify the AI Agent class
class AIAgent:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.messages: list[dict[str, Any]] = []
        self.tools: list[Tool] = []
        print("Agent initialized")


if __name__ == "__main__":
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not set")
        sys.exit(1)
    agent = AIAgent(api_key)

# ```bash
# export OPENAI_API_KEY="your-api-key-here"
# uv run runbook/02_agent_class.py
# ```
# Should print: Agent initialized
