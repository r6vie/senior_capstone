"""In-memory stand-ins for MongoDB and Claude, so onboarding tests need neither Atlas nor an API key."""

from copy import deepcopy
from types import SimpleNamespace

from anthropic.types.beta import BetaMessage, BetaTextBlock, BetaToolUseBlock, BetaUsage


def matches(document: dict, query: dict) -> bool:
    for key, condition in query.items():
        value = document.get(key)
        if isinstance(condition, dict) and "$exists" in condition:
            if (key in document) != condition["$exists"]:
                return False
        elif isinstance(condition, dict) and "$in" in condition:
            if value not in condition["$in"]:
                return False
        elif value != condition:
            return False
    return True


class FakeCursor:
    def __init__(self, documents: list[dict]):
        self.documents = documents

    def sort(self, key: str, direction: int):
        self.documents.sort(key=lambda document: document.get(key), reverse=direction < 0)
        return self

    async def to_list(self, length=None):
        return self.documents if length is None else self.documents[:length]

    def __aiter__(self):
        self.position = 0
        return self

    async def __anext__(self):
        if self.position >= len(self.documents):
            raise StopAsyncIteration
        self.position += 1
        return self.documents[self.position - 1]


class FakeCollection:
    def __init__(self):
        self.documents: dict[str, dict] = {}

    def find(self, query: dict | None = None, projection: dict | None = None) -> FakeCursor:
        return FakeCursor([deepcopy(doc) for doc in self.documents.values() if matches(doc, query or {})])

    async def find_one(self, query: dict, projection: dict | None = None) -> dict | None:
        found = self.find(query).documents
        return found[0] if found else None

    async def insert_one(self, document: dict):
        assert document["_id"] not in self.documents, "duplicate _id"
        self.documents[document["_id"]] = deepcopy(document)
        return SimpleNamespace(inserted_id=document["_id"])

    async def insert_many(self, documents: list[dict]):
        for document in documents:
            await self.insert_one(document)

    async def update_one(self, query: dict, update: dict):
        for document in self.documents.values():
            if matches(document, query):
                document.update(deepcopy(update.get("$set", {})))
                for key, amount in update.get("$inc", {}).items():
                    document[key] = document.get(key, 0) + amount
                return SimpleNamespace(matched_count=1, modified_count=1)
        return SimpleNamespace(matched_count=0, modified_count=0)

    async def delete_one(self, query: dict):
        for key, document in list(self.documents.items()):
            if matches(document, query):
                del self.documents[key]
                return SimpleNamespace(deleted_count=1)
        return SimpleNamespace(deleted_count=0)

    async def delete_many(self, query: dict):
        doomed = [key for key, document in self.documents.items() if matches(document, query)]
        for key in doomed:
            del self.documents[key]
        return SimpleNamespace(deleted_count=len(doomed))


class FakeDatabase:
    def __init__(self):
        self.collections: dict[str, FakeCollection] = {}

    def __getattr__(self, name: str) -> FakeCollection:
        if name.startswith("__"):
            raise AttributeError(name)
        return self.collections.setdefault(name, FakeCollection())


def text(words: str) -> BetaTextBlock:
    return BetaTextBlock(type="text", text=words)


def tool(name: str, tool_input: dict, call_id: str = "call-1") -> BetaToolUseBlock:
    return BetaToolUseBlock(type="tool_use", id=call_id, name=name, input=tool_input)


def reply(*blocks, stop_reason: str | None = None) -> BetaMessage:
    if stop_reason is None:
        stop_reason = "tool_use" if any(block.type == "tool_use" for block in blocks) else "end_turn"
    return BetaMessage(
        id="msg", type="message", role="assistant", model="claude-opus-5-5", content=list(blocks),
        stop_reason=stop_reason, stop_sequence=None, usage=BetaUsage(input_tokens=1, output_tokens=1),
    )


class ScriptedClaude:
    """Plays back prepared responses in order and records every request it was sent."""

    def __init__(self, *responses: BetaMessage):
        self.responses = list(responses)
        self.requests: list[dict] = []

    async def create(self, **params):
        self.requests.append(deepcopy(params))
        if not self.responses:
            raise AssertionError("Claude was called more times than the test scripted.")
        return self.responses.pop(0)
