"""Read-only, provenance-preserving conversation curation preview.

This is a deterministic extractive first slice, NOT an LLM-generated abstract.
It cannot create/approve memory or install a skill. Model-backed synthesis can
be plugged into a future guarded worker task with quotas and explicit review.
"""
import re

PREFERENCE = re.compile(
    r"\b(i prefer|we prefer|my preference|my preferred|i usually|we usually|"
    r"i always|we always|i never|we never|i use|we use|i want|we want|"
    r"we should|let.s use|our convention|our approach|please remember)\b",
    re.IGNORECASE,
)
SKILL = re.compile(
    r"\b(workflow|runbook|repeatable|reproducib|procedure|step.by.step|"
    r"automate|pipeline|notebook|tutorial)\b",
    re.IGNORECASE,
)
DISCARD = re.compile(
    r"\b(dummy|just testing|test message|testing the|testing if|"
    r"forget this|placeholder|lorem ipsum)\b",
    re.IGNORECASE,
)


def _text(item):
    data = item.get("content")
    if isinstance(data, str):
        return data
    if isinstance(data, dict) and isinstance(data.get("text"), str):
        return data["text"]
    return ""


def _excerpt(text, limit):
    text = " ".join(text.split())
    return text if len(text) <= limit else text[:limit - 1].rstrip() + "…"


def _best_statement(text):
    # Never fabricate or interpret a preference from an assistant response.
    chunks = re.split(r"(?<=[.!?])\s+|\n+", text)
    for chunk in chunks:
        if PREFERENCE.search(chunk) and not DISCARD.search(chunk):
            return _excerpt(chunk, 420)
    return None


def preview(conversation):
    """Extract limited review suggestions from the canonical owner-visible record."""
    messages = conversation.get("messages", [])
    user = [m for m in messages if m.get("author_kind") == "user" and _text(m)]
    assistant = [m for m in messages if m.get("author_kind") == "assistant"]
    candidates = []
    seen = set()
    # Inspect the conversation, but never send its content outside ACP.
    for msg in user[-120:]:
        sentence = _best_statement(_text(msg))
        if not sentence or sentence.casefold() in seen:
            continue
        seen.add(sentence.casefold())
        candidates.append({
            "body": sentence,
            "kind": "preference" if re.search(
                r"\b(prefer|preference|usually|always|never|convention)\b",
                sentence, flags=re.IGNORECASE,
            ) else "project_note",
            "source_conversation_id": str(conversation["id"]),
            "source_message_id": str(msg["id"]),
            "source_sequence": msg["sequence"],
        })
        if len(candidates) >= 5:
            break

    # Short source-linked extracts, not a purported semantic model summary.
    topics = []
    for msg in user:
        prompt = _excerpt(_text(msg), 115)
        if prompt and not DISCARD.search(prompt):
            topics.append({"sequence": msg["sequence"], "excerpt": prompt})
        if len(topics) == 5:
            break
    instructions = [
        _excerpt(_text(m), 155)
        for m in user if SKILL.search(_text(m)) and not DISCARD.search(_text(m))
    ][:5]
    skill_draft = None
    if len(instructions) >= 2:
        title = _excerpt(str(conversation.get("title") or "Research workflow"), 80)
        skill_draft = {
            "title": title,
            "markdown": (
                "# Draft workflow: " + title + "\n\n"
                "Status: proposal only; review steps, safety and authorisation.\n\n"
                + "\n".join("- Source request: " + x for x in instructions)
                + "\n\nExecution, permissions and publication require separate review.\n"
            ),
        }

    return {
        "conversation_id": str(conversation["id"]),
        "conversation_title": conversation["title"],
        "review_type": "extractive_preview",
        "user_turns": len(user),
        "assistant_turns": len(assistant),
        "topics": topics,
        "candidates": candidates,
        "skill_draft": skill_draft,
        "note": (
            "Suggested extracts are not approved memories, verified research facts, "
            "or installed skills. Edit before proposing and approve separately."
        ),
    }
