import json
from typing import AsyncIterator

from openai import AsyncOpenAI

from gemi.providers.base import BaseProvider, Chunk, Message


class OpenAICompatProvider(BaseProvider):
    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1", provider_name: str = ""):
        extra_headers = {}
        if "openrouter" in base_url:
            extra_headers["HTTP-Referer"] = "https://github.com/gemi-cli/gemi"
            extra_headers["X-Title"] = "gemi"
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            default_headers=extra_headers or None,
        )

    def update_key(self, api_key: str):
        self.client.api_key = api_key

    async def chat(
        self,
        messages: list[Message],
        tools: list[dict] | None = None,
        model: str | None = None,
        stream: bool = True,
    ) -> AsyncIterator[Chunk]:
        model = model or "gpt-4o-mini"
        formatted_messages = self._build_messages(messages)
        formatted_tools = self.format_tools(tools) if tools else None

        kwargs = {"model": model, "messages": formatted_messages}
        if formatted_tools:
            kwargs["tools"] = formatted_tools

        if stream:
            kwargs["stream"] = True
            response = await self.client.chat.completions.create(**kwargs)
            tool_calls_acc = {}
            async for chunk in response:
                if not chunk.choices:
                    continue
                choice = chunk.choices[0]
                if choice.finish_reason == "error":
                    error_msg = choice.delta.content if choice.delta and choice.delta.content else "Provider returned error"
                    raise Exception(f"Provider returned error: {error_msg}")
                delta = choice.delta
                if not delta:
                    continue
                if delta.content:
                    yield Chunk(text=delta.content)
                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        idx = tc.index
                        if idx not in tool_calls_acc:
                            tool_calls_acc[idx] = {
                                "id": tc.id or "",
                                "function": {"name": "", "arguments": ""},
                            }
                        if tc.id:
                            tool_calls_acc[idx]["id"] = tc.id
                        if tc.function:
                            if tc.function.name:
                                tool_calls_acc[idx]["function"]["name"] = tc.function.name
                            if tc.function.arguments:
                                tool_calls_acc[idx]["function"]["arguments"] += tc.function.arguments

            if tool_calls_acc:
                calls = []
                for tc_data in tool_calls_acc.values():
                    try:
                        tc_data["function"]["arguments"] = json.loads(
                            tc_data["function"]["arguments"]
                        )
                    except json.JSONDecodeError:
                        pass
                    calls.append(tc_data)
                yield Chunk(tool_calls=calls)
        else:
            response = await self.client.chat.completions.create(**kwargs)
            choice = response.choices[0]
            if choice.message.content:
                yield Chunk(text=choice.message.content)
            if choice.message.tool_calls:
                calls = []
                for tc in choice.message.tool_calls:
                    args = tc.function.arguments
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        pass
                    calls.append({
                        "id": tc.id,
                        "function": {
                            "name": tc.function.name,
                            "arguments": args,
                        },
                    })
                yield Chunk(tool_calls=calls)

    def _build_messages(self, messages: list[Message]) -> list[dict]:
        result = []
        for msg in messages:
            entry = {"role": msg.role, "content": msg.content}
            if msg.tool_calls:
                entry["tool_calls"] = [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["function"]["name"],
                            "arguments": json.dumps(tc["function"]["arguments"])
                            if isinstance(tc["function"]["arguments"], dict)
                            else tc["function"]["arguments"],
                        },
                    }
                    for tc in msg.tool_calls
                ]
            if msg.tool_call_id:
                entry["tool_call_id"] = msg.tool_call_id
            if msg.name:
                entry["name"] = msg.name
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
