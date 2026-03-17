import asyncio

from core.pipeline import AgentState, VoicePipeline


class DummyVAD:
    async def is_speech(self, pcm):
        return True if pcm else False


class DummySTT:
    async def stream_transcripts(self, queue):
        words = ["hello", "i", "need", "help", "with", "my", "order"]
        for w in words:
            await queue.get()
            yield {"type": "partial", "text": w}
        yield {"type": "final", "text": "hello i need help with my order"}


class DummyLLM:
    async def stream_sentences(self, prompt):
        _ = prompt
        yield "Sure, I can help with your order."


class DummyTTS:
    async def stream_mulaw_chunks(self, text, chunk_ms=100):
        _ = text, chunk_ms
        yield "Zm9v"


class DummyKB:
    async def search(self, query, top_k=3):
        _ = query, top_k
        return "order support context"


class DummySessions:
    def __init__(self):
        self.turns = []

    async def append_turn(self, sid, role, text):
        self.turns.append((sid, role, text))


class DummyStream:
    def __init__(self):
        self.audio = []
        self.cleared = 0

    async def send_audio(self, payload):
        self.audio.append(payload)

    async def send_clear(self):
        self.cleared += 1


def test_pipeline_response_and_barge_in():
    async def run_case():
        stream = DummyStream()
        sessions = DummySessions()
        pipeline = VoicePipeline("call1", DummyVAD(), DummySTT(), DummyLLM(), DummyTTS(), DummyKB(), sessions, stream)

        run_task = asyncio.create_task(pipeline.start())
        for _ in range(8):
            await pipeline.handle_audio(b"\x01\x00" * 200)
        await asyncio.sleep(0.05)
        await pipeline.handle_audio(b"\x01\x00" * 200)
        await pipeline.audio_in.put(None)
        await asyncio.wait_for(run_task, timeout=1)

        assert stream.audio
        assert pipeline.state in {AgentState.IDLE, AgentState.LISTENING}
        assert any(role == "assistant" for _, role, _ in sessions.turns)

    asyncio.run(run_case())
