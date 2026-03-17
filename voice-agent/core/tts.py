from collections.abc import AsyncIterator

from core.audio import pcm16_to_mulaw_b64


class ElevenLabsTTS:
    def __init__(self, api_key: str, voice_id: str):
        self.api_key = api_key
        self.voice_id = voice_id

    async def synthesize_pcm16(self, text: str) -> bytes:
        # deterministic fake tone payload (mockable in tests)
        return (text.encode("utf-8")[:320] or b"ok") * 20

    async def stream_mulaw_chunks(self, text: str, chunk_ms: int = 100) -> AsyncIterator[str]:
        pcm = await self.synthesize_pcm16(text)
        # 8kHz pcm16 => 16 bytes per ms, so 100ms = 1600 bytes pcm16
        step = max(1600, chunk_ms * 16)
        for i in range(0, len(pcm), step):
            yield pcm16_to_mulaw_b64(pcm[i : i + step])
