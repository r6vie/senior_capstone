"""Stand-ins for outside services, so tests never call Claude or send email."""

from anthropic.types.beta import BetaMessage, BetaTextBlock, BetaUsage

from trove.ai.client import Claude


def text_message(text: str, stop_reason: str = "end_turn") -> BetaMessage:
    """A Messages API response containing one text block."""
    return BetaMessage(
        id="msg_test",
        type="message",
        role="assistant",
        model="claude-opus-5-5",
        content=[BetaTextBlock(type="text", text=text)],
        stop_reason=stop_reason,
        stop_sequence=None,
        usage=BetaUsage(input_tokens=1, output_tokens=1),
    )


class FakeClaude(Claude):
    """Returns scripted responses in order and records every request it was sent."""

    def __init__(self, responses: list[BetaMessage] | None = None, model: str = "claude-opus-5-5"):
        self.model = model
        self.responses = list(responses or [])
        self.requests: list[dict] = []

    async def create(self, **params) -> BetaMessage:
        self.requests.append(self.request(params))
        if not self.responses:
            raise AssertionError("FakeClaude ran out of scripted responses.")
        response = self.responses.pop(0)
        if response.stop_reason == "refusal":
            from trove.ai.client import ClaudeRefused

            raise ClaudeRefused()
        return response


async def waiting_question_id(client, headers) -> str:
    state = (await client.get("/interview", headers=headers)).json()
    question = state.get("question")
    return question["question_id"] if question else "no-question-waiting"


async def send_answer(client, headers, text: str):
    """Answer the waiting question, as a client looking at it would."""
    question_id = await waiting_question_id(client, headers)
    return await client.post(
        "/interview/answers", json={"answer": text, "question_id": question_id}, headers=headers
    )


async def send_skip(client, headers):
    question_id = await waiting_question_id(client, headers)
    return await client.post("/interview/skip", json={"question_id": question_id}, headers=headers)


async def finish_and_wait(client, headers, **body) -> dict:
    """End the interview or round. The writing runs after the response, so read where it got to."""
    response = await client.post("/interview/finish", headers=headers, **({"json": body} if body else {}))
    assert response.status_code == 200, response.text
    return (await client.get("/interview", headers=headers)).json()


async def choose_and_wait(client, headers, title: int) -> dict:
    """Choose a title. The book is written after the response, so read it."""
    response = await client.post("/interview/title", json={"title": title}, headers=headers)
    assert response.status_code == 200, response.text
    return (await client.get("/books/me", headers=headers)).json()
