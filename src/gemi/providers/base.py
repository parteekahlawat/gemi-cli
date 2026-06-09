from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, AsyncIterator


@dataclass
class Chunk:
    text: str = ""
    tool_calls: list[dict] | None = None
    finish_reason: str | None = None


@dataclass
class Message:
    role: str  # "user", "assistant", "system", "tool"
    content: str = ""
    tool_calls: list[dict] | None = None
    tool_call_id: str | None = None
    name: str | None = None


class BaseProvider(ABC):
    @abstractmethod
    async def chat(
        self,
        messages: list[Message],
        tools: list[dict] | None = None,
        model: str | None = None,
        stream: bool = True,
    ) -> AsyncIterator[Chunk]:
        ...

    @abstractmethod
    def format_tools(self, tools: list[dict]) -> list:
        ...
