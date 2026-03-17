import json


class TwilioAudioStream:
    def __init__(self, websocket, stream_sid: str):
        self.websocket = websocket
        self.stream_sid = stream_sid

    async def send_audio(self, mulaw_b64: str):
        await self.websocket.send_text(
            json.dumps(
                {
                    "event": "media",
                    "streamSid": self.stream_sid,
                    "media": {"payload": mulaw_b64},
                }
            )
        )

    async def send_clear(self):
        await self.websocket.send_text(json.dumps({"event": "clear", "streamSid": self.stream_sid}))
