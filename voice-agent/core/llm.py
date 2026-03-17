from collections.abc import AsyncIterator


class GroqLLM:
    def __init__(self, api_key: str, model: str = "llama-3.1-8b-instant"):
        self.api_key = api_key
        self.model = model

    async def stream_answer(self, prompt: str) -> AsyncIterator[str]:
        text = f"I heard: {prompt}. Let me help you quickly."
        for token in text.split():
            yield token + " "

    async def stream_sentences(self, prompt: str) -> AsyncIterator[str]:
        buffer = ""
        async for token in self.stream_answer(prompt):
            buffer += token
            if any(buffer.rstrip().endswith(p) for p in [".", "!", "?"]):
                yield buffer.strip()
                buffer = ""
        if buffer.strip():
            yield buffer.strip()
