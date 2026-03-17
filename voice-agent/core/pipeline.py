import asyncio
import contextlib
from enum import Enum


class AgentState(str, Enum):
    IDLE = "IDLE"
    LISTENING = "LISTENING"
    THINKING = "THINKING"
    SPEAKING = "SPEAKING"


class VoicePipeline:
    def __init__(self, call_sid: str, vad, stt, llm, tts, kb, sessions, stream):
        self.call_sid = call_sid
        self.vad = vad
        self.stt = stt
        self.llm = llm
        self.tts = tts
        self.kb = kb
        self.sessions = sessions
        self.stream = stream

        self.state = AgentState.IDLE
        self.audio_in: asyncio.Queue[bytes | None] = asyncio.Queue()
        self.response_task: asyncio.Task | None = None
        self.partial_words: list[str] = []

    async def start(self):
        await self.sessions.append_turn(self.call_sid, "system", "Session started")
        self.state = AgentState.LISTENING
        async for event in self.stt.stream_transcripts(self.audio_in):
            text = event["text"].strip()
            if event["type"] == "partial":
                self.partial_words.append(text)
                if len(self.partial_words) > 6 and self.response_task is None:
                    await self._begin_response(" ".join(self.partial_words[-8:]))
            elif event["type"] == "final":
                await self.sessions.append_turn(self.call_sid, "user", text)
                if self.response_task is None:
                    await self._begin_response(text)

    async def handle_audio(self, pcm16_8k: bytes):
        is_speech = await self.vad.is_speech(pcm16_8k)
        if is_speech and self.state == AgentState.SPEAKING:
            await self._barge_in()
        await self.audio_in.put(pcm16_8k)

    async def close(self):
        await self.audio_in.put(None)
        if self.response_task:
            self.response_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.response_task

    async def _barge_in(self):
        if self.response_task:
            self.response_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.response_task
            self.response_task = None
        self.state = AgentState.LISTENING
        await self.stream.send_clear()

    async def _begin_response(self, query: str):
        self.state = AgentState.THINKING
        self.response_task = asyncio.create_task(self._respond(query))

    async def _respond(self, query: str):
        context_task = asyncio.create_task(self.kb.search(query, top_k=3))
        context = await context_task
        prompt = f"Context:\n{context}\n\nUser: {query}"

        self.state = AgentState.SPEAKING
        output_text = []
        async for sentence in self.llm.stream_sentences(prompt):
            output_text.append(sentence)
            async for mulaw_b64 in self.tts.stream_mulaw_chunks(sentence, chunk_ms=100):
                await self.stream.send_audio(mulaw_b64)
        await self.sessions.append_turn(self.call_sid, "assistant", " ".join(output_text))
        self.state = AgentState.IDLE
        self.response_task = None
