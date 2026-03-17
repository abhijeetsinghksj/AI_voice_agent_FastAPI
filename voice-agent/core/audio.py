import audioop
import base64
from typing import Iterable


def mulaw_b64_to_pcm16(payload_b64: str) -> bytes:
    mulaw = base64.b64decode(payload_b64)
    return audioop.ulaw2lin(mulaw, 2)


def pcm16_to_mulaw_b64(pcm16: bytes) -> str:
    mulaw = audioop.lin2ulaw(pcm16, 2)
    return base64.b64encode(mulaw).decode("utf-8")


def resample_pcm16(pcm16: bytes, src_rate: int, dst_rate: int, state=None) -> tuple[bytes, object]:
    if src_rate == dst_rate:
        return pcm16, state
    converted, state = audioop.ratecv(pcm16, 2, 1, src_rate, dst_rate, state)
    return converted, state


def chunk_bytes(buffer: bytes, size: int) -> Iterable[bytes]:
    for i in range(0, len(buffer), size):
        yield buffer[i : i + size]
