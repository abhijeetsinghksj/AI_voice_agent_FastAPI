import asyncio
from collections.abc import AsyncIterator


class DeepgramSTT:
    """Mockable async streaming STT facade."""

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def stream_transcripts(self, audio_queue: "asyncio.Queue[bytes]") -> AsyncIterator[dict]:
        words_seen = 0
        while True:
            chunk = await audio_queue.get()
            if chunk is None:
                break
            words_seen += 1
            partial = f"word{words_seen}"
            yield {"type": "partial", "text": partial}
            if words_seen % 4 == 0:
                yield {"type": "final", "text": " ".join(f"word{i}" for i in range(words_seen - 3, words_seen + 1))}
