import json

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import PlainTextResponse

from core.audio import mulaw_b64_to_pcm16, resample_pcm16
from core.pipeline import VoicePipeline
from telephony.audio_stream import TwilioAudioStream

router = APIRouter()


@router.post("/twilio/incoming", response_class=PlainTextResponse)
async def incoming_call(request: Request):
    host = request.headers.get("host", "localhost:8080")
    twiml = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
        "<Response><Connect>"
        f"<Stream url=\"wss://{host}/twilio/stream/{{{{CallSid}}}}\" />"
        "</Connect></Response>"
    )
    return twiml


@router.websocket("/twilio/stream/{call_sid}")
async def twilio_stream(websocket: WebSocket, call_sid: str):
    await websocket.accept()
    app_state = websocket.app.state
    resample_state = None
    stream_sid = ""
    pipeline = None

    try:
        while True:
            raw = await websocket.receive_text()
            event = json.loads(raw)
            event_type = event.get("event")

            if event_type == "start":
                stream_sid = event["start"]["streamSid"]
                pipeline = VoicePipeline(
                    call_sid=call_sid,
                    vad=app_state.vad,
                    stt=app_state.stt,
                    llm=app_state.llm,
                    tts=app_state.tts,
                    kb=app_state.kb,
                    sessions=app_state.sessions,
                    stream=TwilioAudioStream(websocket, stream_sid),
                )
                app_state.bg.create_task(pipeline.start())
            elif event_type == "media" and pipeline:
                pcm8k = mulaw_b64_to_pcm16(event["media"]["payload"])
                pcm16k, resample_state = resample_pcm16(pcm8k, src_rate=8000, dst_rate=16000, state=resample_state)
                await pipeline.handle_audio(pcm16k)
            elif event_type == "stop" and pipeline:
                await pipeline.close()
                break
    except WebSocketDisconnect:
        if pipeline:
            await pipeline.close()
