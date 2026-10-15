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


# Specify the model for our tools (a standardized way to define the interface for tools that the AI Agent can use)
class Tool(BaseModel):
    name: str
    description: str
    input_schema: dict[str, Any]


# Specify the AI Agent class - include internal function to set up the tools we want.
class AIAgent:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.messages: list[dict[str, Any]] = []
        self.tools: list[Tool] = []
        self._setup_tools()
        print(f"Agent initialized with {len(self.tools)} tools")

    """
    # Internal function to set up the tools we want the AI Agent to have access to:
    --------------------------------------------------------------------------------
    We are keeping this very basic. What are the minimal things a coding agent needs to do? 
    At a basic level, we give the coding agent the following 3 tools: 
        read_file
        list_files
        edit_file
    """

    def _setup_tools(self):
        self.tools = [
            Tool(
                name="read_file",
                description="Read the contents of a file at the specified path",
                # All we really need to give it is a path! Python does the rest.
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "The path to the file to read",
                        }
                    },
                    "required": ["path"],
                },
            ),
            Tool(
                name="list_files",
                description="List all files and directories in the specified path",
                # All we really need to give it is a path! Python does the rest.
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "The directory path to list (defaults to current directory)",
                        }
                    },
                    "required": [],
                },
            ),
            Tool(
                name="edit_file",
                description="Edit a file by replacing old_text with new_text. Creates the file if it doesn't exist.",
                # Now we need more than the path. We need to provide old text and new text
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "The path to the file to edit",
                        },
                        "old_text": {
                            "type": "string",
                            "description": "The text to search for and replace (leave empty to create new file)",
                        },
                        "new_text": {
                            "type": "string",
                            "description": "The text to replace old_text with",
                        },
                    },
                    "required": ["path", "new_text"],
                },
            ),
        ]


if __name__ == "__main__":
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not set")
        sys.exit(1)
    agent = AIAgent(api_key)


# ```bash
# export OPENAI_API_KEY="your-api-key-here"
# uv run runbook/03_define_tools.py
# ```
# Should print: Agent initialized with 3 tools
