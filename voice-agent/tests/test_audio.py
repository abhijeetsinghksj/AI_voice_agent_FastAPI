from core.audio import mulaw_b64_to_pcm16, pcm16_to_mulaw_b64, resample_pcm16


def test_mulaw_roundtrip():
    pcm = (b"\x01\x00" * 400)
    b64 = pcm16_to_mulaw_b64(pcm)
    restored = mulaw_b64_to_pcm16(b64)
    assert len(restored) == len(pcm)


def test_resample_pcm16():
    pcm = (b"\x01\x00" * 800)
    up, state = resample_pcm16(pcm, 8000, 16000)
    assert len(up) > len(pcm)
    down, _ = resample_pcm16(up, 16000, 8000, state)
    assert len(down) > 0
