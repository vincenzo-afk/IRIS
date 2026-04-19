"""
IRIS — Voice Module
====================
Handles:
  - Speech-to-Text (STT) via faster-whisper (local) or SpeechRecognition
  - Text-to-Speech (TTS) via pyttsx3 / ElevenLabs / gTTS
  - Wake word detection ("hey iris")
  - Continuous microphone listener thread
"""

import io
import os
import queue
import threading
import time
import logging
import tempfile
from typing import Callable, Optional

import numpy as np
import sounddevice as sd

from config import (
    STT_MODEL,
    TTS_ENGINE,
    ELEVENLABS_API_KEY,
    ELEVENLABS_VOICE_ID,
    TTS_RATE,
    WAKE_WORD,
)

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────
# TTS ENGINES
# ──────────────────────────────────────────────────────────────

def _init_pyttsx3():
    import pyttsx3
    engine = pyttsx3.init()
    engine.setProperty("rate", TTS_RATE)
    voices = engine.getProperty("voices")
    # Prefer a female-ish voice if available
    for v in voices:
        if "zira" in v.id.lower() or "hazel" in v.id.lower() or "female" in v.id.lower():
            engine.setProperty("voice", v.id)
            break
    return engine


_pyttsx3_engine = None
_pyttsx3_lock = threading.Lock()


def speak(text: str):
    """
    Convert text to speech using the configured TTS engine.
    Blocks until speech is finished.
    """
    if not text.strip():
        return
    logger.info("[IRIS TTS] %s", text)

    engine = TTS_ENGINE.lower()

    if engine == "pyttsx3":
        global _pyttsx3_engine
        with _pyttsx3_lock:
            if _pyttsx3_engine is None:
                _pyttsx3_engine = _init_pyttsx3()
            _pyttsx3_engine.say(text)
            _pyttsx3_engine.runAndWait()

    elif engine == "elevenlabs" and ELEVENLABS_API_KEY:
        try:
            from elevenlabs import generate, play
            audio = generate(
                text=text,
                voice=ELEVENLABS_VOICE_ID,
                api_key=ELEVENLABS_API_KEY,
            )
            play(audio)
        except Exception as exc:
            logger.error("ElevenLabs TTS failed: %s — falling back to pyttsx3", exc)
            _speak_pyttsx3_fallback(text)

    elif engine == "gtts":
        try:
            from gtts import gTTS
            import pygame
            tts = gTTS(text=text, lang="en")
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                tts.save(f.name)
                tmp = f.name
            pygame.mixer.init()
            pygame.mixer.music.load(tmp)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            os.unlink(tmp)
        except Exception as exc:
            logger.error("gTTS failed: %s — falling back to pyttsx3", exc)
            _speak_pyttsx3_fallback(text)

    else:
        _speak_pyttsx3_fallback(text)


def _speak_pyttsx3_fallback(text: str):
    global _pyttsx3_engine
    with _pyttsx3_lock:
        if _pyttsx3_engine is None:
            _pyttsx3_engine = _init_pyttsx3()
        _pyttsx3_engine.say(text)
        _pyttsx3_engine.runAndWait()


# ──────────────────────────────────────────────────────────────
# STT — faster-whisper
# ──────────────────────────────────────────────────────────────

_whisper_model = None
_whisper_lock = threading.Lock()


def _get_whisper():
    global _whisper_model
    with _whisper_lock:
        if _whisper_model is None:
            try:
                from faster_whisper import WhisperModel
                _whisper_model = WhisperModel(
                    STT_MODEL, device="cpu", compute_type="int8"
                )
                logger.info("Whisper model '%s' loaded", STT_MODEL)
            except ImportError:
                logger.warning(
                    "faster-whisper not installed — STT will be limited"
                )
    return _whisper_model


def transcribe_audio(audio_data: np.ndarray, sample_rate: int = 16000) -> str:
    """
    Transcribe a numpy audio array using faster-whisper.
    Returns the transcribed string (may be empty).
    """
    model = _get_whisper()
    if model is None:
        return ""

    # Save to a temp WAV file (faster-whisper accepts file paths)
    import soundfile as sf
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        tmp_path = f.name
    try:
        sf.write(tmp_path, audio_data, sample_rate)
        segments, _ = model.transcribe(tmp_path, beam_size=5)
        text = " ".join(s.text.strip() for s in segments)
        return text.strip()
    finally:
        os.unlink(tmp_path)


def record_until_silence(
    sample_rate: int = 16000,
    silence_threshold: float = 0.01,
    silence_duration: float = 1.5,
    max_duration: float = 30.0,
) -> np.ndarray:
    """
    Record microphone audio until silence is detected.
    Returns a numpy float32 array.
    """
    chunk_size = int(sample_rate * 0.1)  # 100ms chunks
    frames = []
    silent_chunks = 0
    max_silent = int(silence_duration / 0.1)

    logger.debug("Recording...")
    with sd.InputStream(samplerate=sample_rate, channels=1, dtype="float32") as stream:
        elapsed = 0.0
        while elapsed < max_duration:
            chunk, _ = stream.read(chunk_size)
            frames.append(chunk.copy())
            rms = np.sqrt(np.mean(chunk ** 2))
            if rms < silence_threshold:
                silent_chunks += 1
                if silent_chunks >= max_silent and len(frames) > max_silent:
                    break
            else:
                silent_chunks = 0
            elapsed += 0.1

    audio = np.concatenate(frames, axis=0).flatten()
    return audio


def listen_once() -> str:
    """Record one utterance and return transcription."""
    audio = record_until_silence()
    return transcribe_audio(audio)


# ──────────────────────────────────────────────────────────────
# WAKE WORD LISTENER
# ──────────────────────────────────────────────────────────────

class VoiceListener:
    """
    Background thread that continuously listens for the wake word.
    When detected, it records the command and fires `on_command(text)`.
    """

    def __init__(
        self,
        on_command: Callable[[str], None],
        wake_word: str = WAKE_WORD,
    ):
        self.on_command = on_command
        self.wake_word = wake_word.lower()
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self.active = True            # Set False to mute even when running

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        logger.info("VoiceListener started (wake_word='%s')", self.wake_word)

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)
        logger.info("VoiceListener stopped")

    def _loop(self):
        while self._running:
            try:
                if not self.active:
                    time.sleep(0.5)
                    continue

                audio = record_until_silence(
                    silence_duration=0.8,   # shorter for wake-word phase
                    max_duration=8.0,
                )
                text = transcribe_audio(audio).lower()

                if not text:
                    continue

                logger.debug("Heard: %s", text)

                if self.wake_word in text:
                    # Strip the wake word and pass only the command
                    command = text.replace(self.wake_word, "").strip()

                    if not command:
                        speak("Yes? I'm listening.")
                        audio2 = record_until_silence(max_duration=20.0)
                        command = transcribe_audio(audio2)

                    if command:
                        logger.info("[WAKE] Command: %s", command)
                        self.on_command(command)

            except Exception as exc:
                logger.error("VoiceListener error: %s", exc)
                time.sleep(1)
