#!/usr/bin/eny python
# -*- coding: utf-8 -*-
"""
@Time    :2025/11/22 21:05
#Author  :Emcikem
@File    :deepseek2.py
"""
import json

import dotenv
from openai import OpenAI

dotenv.load_dotenv()


def calculator(expression: str) -> str:
    """一个简单的计算几，可以执行数学表达式"""
    try:
        result = eval(expression)
        return json.dumps({"result": result})
    except Exception as e:
        return json.dumps({"error": f"无效表达式，错误信息：{str(e)}"})


class ReActAgent:
    def __init__(self):
        self.client = OpenAI()
        self.messages = [
            {
                "role": "user",
                "content": "你好，你是？"
            }
        ]
        self.model = "deepseek-chat"
        self.available_tools = {"calculator": calculator}
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "calculator",
                    "description": "一个可以计算数学表达式的计算器",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "expression": {
                                "type": "string",
                                "description": "需要计算的数学表达式，例如：123+456+789"
                            }
                        },
                        "required": ["expression"]
                    }
                }
            }
        ]

    def process_query(self, query: str) -> str:
        """使用deepseek处理用户输出"""
        self.messages.append({"role": "user", "content": query})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            tools=self.tools,
        )

        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        if tool_calls:
            self.messages.append(response_message.model_dump())

            for tool_call in tool_calls:
                print("tool_call", tool_call.function.name)
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                function_to_call = self.available_tools.get(tool_name)

                result = function_to_call(**tool_args)
                print(f"tool [{tool_name}] result: {result}")

                self.messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": tool_name,
                    "content": result
                })

            second_response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                tools=self.tools,
                tool_choice="none",
            )

            self.messages.append(second_response.choices[0].message.model_dump())
            return "Assistant: " + second_response.choices[0].message.content

        else:
            return "Assistant: " + response_message.content

    def chat_loop(self):
        while True:
            try:
                query = input("\nQuery: ").strip()
                if query.lower() == "quit":
                    break
                print(self.process_query(query))
            except Exception as e:
                print(f"\nError: {str(e)}")


if __name__ == '__main__':
    ReActAgent().chat_loop()
