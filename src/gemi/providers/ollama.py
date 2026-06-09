import json
from typing import AsyncIterator

import ollama as ollama_sdk

from gemi.providers.base import BaseProvider, Chunk, Message


class OllamaProvider(BaseProvider):
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.client = ollama_sdk.AsyncClient(host=base_url)

    async def chat(
        self,
        messages: list[Message],
        tools: list[dict] | None = None,
        model: str | None = None,
        stream: bool = True,
    ) -> AsyncIterator[Chunk]:
        model = model or "llama3"
        formatted_messages = self._build_messages(messages)
        formatted_tools = self.format_tools(tools) if tools else None

        if stream and not formatted_tools:
            async for part in await self.client.chat(
                model=model,
                messages=formatted_messages,
                stream=True,
            ):
                if part.get("message", {}).get("content"):
                    yield Chunk(text=part["message"]["content"])
        else:
            response = await self.client.chat(
                model=model,
                messages=formatted_messages,
                tools=formatted_tools,
                stream=False,
            )
            msg = response.get("message", {})
            if msg.get("content"):
                yield Chunk(text=msg["content"])
            if msg.get("tool_calls"):
                for tc in msg["tool_calls"]:
                    yield Chunk(tool_calls=[{
                        "id": tc["function"]["name"],
                        "function": {
                            "name": tc["function"]["name"],
                            "arguments": tc["function"]["arguments"],
                        },
                    }])

    def _build_messages(self, messages: list[Message]) -> list[dict]:
        result = []
        for msg in messages:
            entry = {"role": msg.role, "content": msg.content}
            if msg.role == "tool":
                entry["role"] = "tool"
            result.append(entry)
        return result

    def format_tools(self, tools: list[dict]) -> list[dict]:
        formatted = []
        for tool in tools:
            formatted.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("parameters", {}),
                },
            })
        return formatted
