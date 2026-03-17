from dataclasses import dataclass


@dataclass
class VADState:
    speaking: bool = False


class SileroVAD:
    """Lightweight energy-based VAD wrapper with silero-style interface."""

    def __init__(self, threshold: int = 180):
        self.threshold = threshold

    async def is_speech(self, pcm16: bytes) -> bool:
        if not pcm16:
            return False
        # async-friendly: no blocking IO, CPU tiny
        total = 0
        samples = len(pcm16) // 2
        for i in range(0, len(pcm16), 2):
            sample = int.from_bytes(pcm16[i : i + 2], "little", signed=True)
            total += abs(sample)
        return (total / max(samples, 1)) > self.threshold
