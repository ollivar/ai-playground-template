# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "openai",
#     "pydantic",
# ]
# ///

"""
A simple AI agent using OpenAI.

The agent can:
- Read files
- List files and directories
- Edit or create files

Uses OpenAI function calling to execute tools.
"""

import json
import os
import sys
import argparse  # NEW
import logging  # NEW
from typing import Any

from openai import OpenAI
from pydantic import BaseModel


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[
        logging.FileHandler("agent.log", encoding="utf-8"),
    ],
    force=True,
)

# Suppress HTTP request logging
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

# Create an application-specific logger
logger = logging.getLogger("AIAgent")


class Tool(BaseModel):
    name: str
    description: str
    input_schema: dict[str, Any]


class AIAgent:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-4.1-nano")
        self.messages: list[dict[str, Any]] = [
            {
                "role": "developer",
                "content": (
                    "You are a helpful coding assistant operating in a terminal environment. "
                    "Output only plain text without markdown formatting, as your responses "
                    "appear directly in the terminal. "
                    "Be thorough, providing clear and practical advice. "
                    "Use a friendly tone. "
                    "Format the responses that have more than one answer with asterisks as bullets."
                ),
            }
        ]
        self.tools: list[Tool] = []
        self.max_tool_rounds = 5
        self._setup_tools()

    def _setup_tools(self):
        self.tools = [
            Tool(
                name="read_file",
                description="Read the contents of a file at the specified path",
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
                description=(
                    "List files and directories. "
                    "Use path='.' for the current working directory. "
                    "If no path is provided, use the current directory."
                ),
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

    def _execute_tool(self, tool_name: str, tool_input: dict[str, Any]) -> str:
        try:
            if tool_name == "read_file":
                return self._read_file(tool_input["path"])
            elif tool_name == "list_files":
                return self._list_files(tool_input.get("path", "."))
            elif tool_name == "edit_file":
                return self._edit_file(
                    tool_input["path"],
                    tool_input.get("old_text", ""),
                    tool_input["new_text"],
                )
            else:
                return f"Unknown tool: {tool_name}"
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"

    def _read_file(self, path: str) -> str:
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            return f"File contents of {path}:\n{content}"
        except FileNotFoundError:
            return f"File not found: {path}"
        except Exception as e:
            return f"Error reading file: {str(e)}"

    def _list_files(self, path: str) -> str:
        try:
            if not os.path.exists(path):
                return f"Path not found: {path}"

            items = []
            for item in sorted(os.listdir(path)):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    items.append(f"[DIR]  {item}/")
                else:
                    items.append(f"[FILE] {item}")

            if not items:
                return f"Empty directory: {path}"

            return f"Contents of {path}:\n" + "\n".join(items)
        except Exception as e:
            return f"Error listing files: {str(e)}"

    def _edit_file(self, path: str, old_text: str, new_text: str) -> str:
        try:
            if os.path.exists(path) and old_text:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()

                if old_text not in content:
                    return f"Text not found in file: {old_text}"

                content = content.replace(old_text, new_text)

                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)

                return f"Successfully edited {path}"
            else:
                # Only create directory if path contains subdirectories
                dir_name = os.path.dirname(path)
                if dir_name:
                    os.makedirs(dir_name, exist_ok=True)

                with open(path, "w", encoding="utf-8") as f:
                    f.write(new_text)

                return f"Successfully created {path}"
        except Exception as e:
            return f"Error editing file: {str(e)}"

    def chat(self, user_input: str) -> str:

        logger.info("USER: %s", user_input)

        self.messages.append({"role": "user", "content": user_input})

        logger.info("Conversation contains %d messages", len(self.messages))

        # Convert our Tool objects into OpenAI function definitions.
        tool_schemas = [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.input_schema,
                },
            }
            for tool in self.tools
        ]

        for _ in range(self.max_tool_rounds + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=self.messages,
                    tools=tool_schemas,
                    tool_choice="auto",
                    max_completion_tokens=1000,
                )

                # Print token usage for monitoring.
                if response.usage:
                    logger.info(
                        "TOKEN USAGE - Input: %d, Output: %d, Total: %d",
                        response.usage.prompt_tokens,
                        response.usage.completion_tokens,
                        response.usage.total_tokens,
                    )
                assistant_message = response.choices[0].message

                logger.info("ASSISTANT RESPONSE: %s", assistant_message.content)

                # Store the assistant response in conversation history.
                self.messages.append(assistant_message.model_dump(exclude_none=True))

                # Check whether the model requested any tools.
                if not assistant_message.tool_calls:
                    return assistant_message.content or ""

                # Stop before executing more tools if we've
                # reached our configured limit.
                if _ >= self.max_tool_rounds:
                    return "Agent stopped: maximum tool rounds reached."

                # Execute each requested tool.
                for tool_call in assistant_message.tool_calls:
                    tool_name = tool_call.function.name

                    print(f"[Tool] Executing: {tool_name}")

                    try:
                        tool_input = json.loads(tool_call.function.arguments)

                        if not isinstance(tool_input, dict):
                            raise ValueError("Tool arguments must be an object")

                        logger.info("TOOL CALL: %s", tool_name)
                        logger.info("TOOL ARGUMENTS: %s", tool_input)

                        result = self._execute_tool(
                            tool_name,
                            tool_input,
                        )

                        logger.info("TOOL RESULT: %s", result)

                    except (json.JSONDecodeError, ValueError) as e:
                        result = f"Invalid tool arguments: {e}"

                    # Return the result to OpenAI.
                    self.messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result,
                        }
                    )

            except Exception as e:
                logger.exception("Error during agent execution")
                return f"Error: {str(e)}"

        return "Agent stopped."


# NEW: Build a CLI tool so users can iterate and actually chat from the command line.
def main():
    parser = argparse.ArgumentParser(
        description="AI Code Assistant - A conversational AI agent with file editing capabilities"
    )
    parser.add_argument(
        "--api-key", help="OpenAI API key (or set OPENAI_API_KEY env var)"
    )
    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print(
            "Error: Please provide an API key via --api-key or OPENAI_API_KEY environment variable"
        )
        sys.exit(1)

    agent = AIAgent(api_key)

    print("AI Code Assistant")
    print("=================")
    print("A conversational AI agent that can read, list, and edit files.")
    print("Type 'exit' or 'quit' to end the conversation.")
    print()

    while True:
        try:
            user_input = input("You: ").strip()

            if user_input.lower() in ["exit", "quit"]:
                print("Goodbye!")
                break

            if not user_input:
                continue

            print("\nAssistant: ", end="", flush=True)
            response = agent.chat(user_input)
            print(response)
            print()

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {str(e)}")
            print()


if __name__ == "__main__":
    main()


# ```bash
# export OPENAI_API_KEY="your-api-key-here"
# uv run runbook/06_create_interactive_cli.py
# ```
# Should print:
# AI Code Assistant
# ================
# A conversational AI agent that can read, list, and edit files.
# Type 'exit' or 'quit' to end the conversation.

# You: <<Your input here>>
# ===============
# Type `exit` or `quit` to end the conversation.
