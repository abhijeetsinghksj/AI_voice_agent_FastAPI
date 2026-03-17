import asyncio
from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi import FastAPI

from config import get_settings
from core.llm import GroqLLM
from core.stt import DeepgramSTT
from core.tts import ElevenLabsTTS
from core.vad import SileroVAD
from rag.kb_service import KnowledgeBaseService
from state.session import SessionStore
from telephony.twilio_handler import router as twilio_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    s = get_settings()
    app.state.bg = asyncio.get_running_loop()
    app.state.vad = SileroVAD()
    app.state.stt = DeepgramSTT(s.deepgram_api_key)
    app.state.llm = GroqLLM(s.groq_api_key)
    app.state.tts = ElevenLabsTTS(s.elevenlabs_api_key, s.elevenlabs_voice_id)

    app.state.kb = KnowledgeBaseService(s.faiss_index_path, s.faiss_meta_path)
    await app.state.kb.load()

    redis_client = redis.from_url(s.redis_url, decode_responses=True)
    app.state.sessions = SessionStore(redis_client)

    yield

    await redis_client.close()


app = FastAPI(title="Voice Agent", lifespan=lifespan)
app.include_router(twilio_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
