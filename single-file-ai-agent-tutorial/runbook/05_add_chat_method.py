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
from typing import Any

from openai import OpenAI
from pydantic import BaseModel


class Tool(BaseModel):
    name: str
    description: str
    input_schema: dict[str, Any]


class AIAgent:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-4.1-nano")
        self.messages: list[dict[str, Any]] = []
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

    """
    Takes user input as a string, and create a loop that we can actually use to chat with our agent in the terminal. 
    To do this, we use the OpenAI SDK that has our client that we will use to send requests back-and-forth, store messages, use tools, etc. 
    This is how we manage our conversation. 
    Remember - we initialized our agent with an empty "messages" parameter. We will now start populating this field with the chat method! 
    
        1. User asks a question
        2. We append the question to "messages" list in the standard OpenAI dict format {"role":"user", "content":user_input}
        3. Loop over tools & convert them to OpenAI specification (our model) <---------------- ???
        4. Start a chat loop:
            a. Send user input to our model & specify the tools & parameters
            b. Create a placeholder for chat assistant's message in dict format {"role":"assistant", "content":[]}
            c. Parse the content to determine what to do next. 
                If content.type is text: 
                    return response
                If content.type is tool_use (meaning, the agent decided that they need to *do* something and use a tool): 
                select the tool <------------- ????
                add the tool to the response
                return response
        5. Append the response to the chat assistant's messages list. This is the beginning part of the chat!  
        6. If there is tool use, we execute the tool
            append the results of the tool to response
        
    """

    def chat(self, user_input: str) -> str:
        self.messages.append({"role": "user", "content": user_input})

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
                    print(
                        f"[Tokens] "
                        f"Input: {response.usage.prompt_tokens}, "
                        f"Output: {response.usage.completion_tokens}"
                    )

                assistant_message = response.choices[0].message

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

                        result = self._execute_tool(
                            tool_name,
                            tool_input,
                        )
                        print(f"[DEBUG] Tool arguments: {tool_input}")
                        print(f"[DEBUG] Tool result: {result}")

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
                return f"Error: {str(e)}"

        return "Agent stopped."


if __name__ == "__main__":
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not set")
        sys.exit(1)
    agent = AIAgent(api_key)

    # Test
    print(f"Current working directory: {os.getcwd()}")
    print(agent._list_files("."))

    # Test chat - In this case, it should know to use list_files tool!
    # response = agent.chat("What files are in the current directory?")
    # print("\nAgent Response:")
    # print(response)

    # Test chat - In this case, it should know to use list_files tool!
    response = agent.chat("Explain in a little bit of details what can you help with?")
    print("\nAgent Response:")
    print(response)


# ```bash
# export OPENAI_API_KEY="your-api
# uv run runbook/05_add_chat_method.py
# ```
# Should print a response from Claude listing the files in the directory
