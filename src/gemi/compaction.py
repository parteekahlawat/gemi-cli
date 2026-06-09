from gemi.providers.base import Message

CHARS_PER_TOKEN = 4


def estimate_tokens(messages: list[Message]) -> int:
    total_chars = sum(len(m.content or "") for m in messages)
    return total_chars // CHARS_PER_TOKEN


def needs_compaction(messages: list[Message], max_tokens: int) -> bool:
    used = estimate_tokens(messages)
    return used > int(max_tokens * 0.75)


def compact_messages(messages: list[Message], max_tokens: int) -> list[Message]:
    system_msg = messages[0] if messages and messages[0].role == "system" else None
    conversation = messages[1:] if system_msg else messages[:]

    if len(conversation) < 6:
        return messages

    keep_recent = max(4, len(conversation) // 3)
    old_messages = conversation[:-keep_recent]
    recent_messages = conversation[-keep_recent:]

    summary_parts = []
    for msg in old_messages:
        if msg.role == "user":
            summary_parts.append(f"- User asked: {_truncate(msg.content, 100)}")
        elif msg.role == "assistant" and msg.content:
            summary_parts.append(f"- Assistant: {_truncate(msg.content, 100)}")
        elif msg.role == "tool":
            summary_parts.append(f"- Tool ({msg.name}): {_truncate(msg.content, 60)}")

    summary_text = (
        "[Earlier conversation summary]\n"
        + "\n".join(summary_parts[-20:])
        + "\n[End of summary — conversation continues below]"
    )

    summary_msg = Message(role="user", content=summary_text)
    result = ([system_msg] if system_msg else []) + [summary_msg] + recent_messages

    if estimate_tokens(result) > max_tokens * 0.8:
        return _aggressive_compact(result, max_tokens, system_msg)

    return result


def _aggressive_compact(messages: list[Message], max_tokens: int, system_msg: Message | None) -> list[Message]:
    conversation = messages[1:] if system_msg else messages[:]

    for msg in conversation:
        if msg.role == "tool" and msg.content and len(msg.content) > 500:
            msg.content = msg.content[:500] + "\n... (truncated)"

    return ([system_msg] if system_msg else []) + conversation


def _truncate(text: str | None, length: int) -> str:
    if not text:
        return ""
    text = text.strip().replace("\n", " ")
    if len(text) <= length:
        return text
    return text[:length] + "..."
