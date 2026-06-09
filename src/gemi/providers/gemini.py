import json
from typing import AsyncIterator

from google import genai
from google.genai import types

from gemi.providers.base import BaseProvider, Chunk, Message


class GeminiProvider(BaseProvider):
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)

    def update_key(self, api_key: str):
        self.client = genai.Client(api_key=api_key)

    async def chat(
        self,
        messages: list[Message],
        tools: list[dict] | None = None,
        model: str | None = None,
        stream: bool = True,
    ) -> AsyncIterator[Chunk]:
        model = model or "gemini-2.5-flash"
        contents = self._build_contents(messages)
        formatted_tools = self.format_tools(tools) if tools else None

        config = types.GenerateContentConfig()
        if formatted_tools:
            config.tools = formatted_tools

        system_msgs = [m for m in messages if m.role == "system"]
        if system_msgs:
            config.system_instruction = system_msgs[0].content

        if stream:
            stream_response = await self.client.aio.models.generate_content_stream(
                model=model,
                contents=contents,
                config=config,
            )
            async for response in stream_response:
                if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                    for part in response.candidates[0].content.parts:
                        if part.text:
                            yield Chunk(text=part.text)
                        elif part.function_call:
                            yield Chunk(tool_calls=[{
                                "id": part.function_call.name,
                                "function": {
                                    "name": part.function_call.name,
                                    "arguments": dict(part.function_call.args) if part.function_call.args else {},
                                },
                            }])
        else:
            response = await self.client.aio.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            )
            if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if part.text:
                        yield Chunk(text=part.text)
                    elif part.function_call:
                        yield Chunk(tool_calls=[{
                            "id": part.function_call.name,
                            "function": {
                                "name": part.function_call.name,
                                "arguments": dict(part.function_call.args) if part.function_call.args else {},
                            },
                        }])

    def _build_contents(self, messages: list[Message]) -> list:
        contents = []
        for msg in messages:
            if msg.role == "system":
                continue
            elif msg.role == "user":
                contents.append(types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=msg.content)],
                ))
            elif msg.role == "assistant":
                parts = []
                if msg.content:
                    parts.append(types.Part.from_text(text=msg.content))
                if msg.tool_calls:
                    for tc in msg.tool_calls:
                        parts.append(types.Part.from_function_call(
                            name=tc["function"]["name"],
                            args=tc["function"]["arguments"],
                        ))
                if parts:
                    contents.append(types.Content(role="model", parts=parts))
            elif msg.role == "tool":
                contents.append(types.Content(
                    role="user",
                    parts=[types.Part.from_function_response(
                        name=msg.name or "unknown",
                        response={"result": msg.content},
                    )],
                ))
        return contents

    def format_tools(self, tools: list[dict]) -> list:
        declarations = []
        for tool in tools:
            props = {}
            required = tool.get("parameters", {}).get("required", [])
            for pname, pdef in tool.get("parameters", {}).get("properties", {}).items():
                schema_type = pdef.get("type", "string").upper()
                props[pname] = types.Schema(
                    type=schema_type,
                    description=pdef.get("description", ""),
                )
            declarations.append(types.FunctionDeclaration(
                name=tool["name"],
                description=tool.get("description", ""),
                parameters=types.Schema(
                    type="OBJECT",
                    properties=props,
                    required=required,
                ) if props else None,
            ))
        return [types.Tool(function_declarations=declarations)]
