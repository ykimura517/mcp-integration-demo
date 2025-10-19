import os
import json
from openai import AsyncOpenAI
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
from fastmcp import Client
from mcp.types import ImageContent, TextContent

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

aclient = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MCP_SERVER_URL = "http://mcp_server:9000/sse"


class ChatRequest(BaseModel):
    messages: List[Dict[str, Any]]


async def get_mcp_tools():
    """MCPサーバーからツール定義を取得し、OpenAIの形式に変換する"""
    async with Client(MCP_SERVER_URL) as client:
        tools = await client.list_tools()
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema,
                },
            }
            for tool in tools
        ]


async def call_mcp_tool(tool_name: str, tool_args: dict):
    """MCPサーバーのツールを呼び出す"""
    print(f"Calling MCP tool: {tool_name} with args: {tool_args}")
    async with Client(MCP_SERVER_URL) as client:
        return await client.call_tool(tool_name, tool_args)


@app.post("/api/chat")
async def chat(request: ChatRequest):
    messages = request.messages
    tools = await get_mcp_tools()
    image_url = None
    iter_num = 5  # 何らかの理由で無限ループして大量課金されないように上限を設定
    while iter_num > 0:
        iter_num -= 1
        # ツール使用判断
        response = await aclient.chat.completions.create(
            model="gpt-5",
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )
        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        if not tool_calls:
            return {
                "role": "assistant",
                "content": response_message.content,
                "imageUrl": image_url,
            }

        # 以下、ツール呼び出し時の処理
        image_url = None
        messages.append(response_message)
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)

            # MCPツールを呼び出し
            mcp_results = await call_mcp_tool(function_name, function_args)

            content = ""
            # 結果を処理
            from pprint import pprint

            if not mcp_results:
                raise RuntimeError("MCP tool returned no results")
            for result in mcp_results.content:
                if isinstance(result, ImageContent):
                    base64_image = result.data
                    image_url = f"data:image/png;base64,{base64_image}"
                    content += f"グラフ画像を生成しました。以降、グラフ作成は不要です。"
                elif isinstance(result, TextContent):
                    content += result.text
                else:
                    raise NotImplementedError(
                        f"Unsupported content type: {type(result)}"
                    )

            messages.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": content,
                }
            )
    raise RuntimeError("Exceeded maximum tool call iterations")
