"""
Local GPU-Accelerated Transcriber for HyperClip.
Uses faster-whisper with NVIDIA CUDA acceleration on the RTX 3050 (or CPU fallback).
Extracts word-level timestamps for animated captions and surgical video cuts.
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger("hyperclip.transcriber")

class LocalTranscriber:
    def __init__(self, model_size: str = "base", device: str = "auto"):
        self.model_size = model_size
        self.device = device
        self._model = None

    def _load_model(self):
        if self._model is not None:
            return self._model
            
        from faster_whisper import WhisperModel
        import torch

        if self.device == "auto":
            use_cuda = torch.cuda.is_available()
            selected_device = "cuda" if use_cuda else "cpu"
            compute_type = "float16" if use_cuda else "int8"
        else:
            selected_device = self.device
            compute_type = "float16" if selected_device == "cuda" else "int8"

        logger.info(f"Loading faster-whisper '{self.model_size}' on {selected_device} ({compute_type})...")
        self._model = WhisperModel(self.model_size, device=selected_device, compute_type=compute_type)
        return self._model

    def transcribe(self, audio_path: str, language: str = None) -> Dict[str, Any]:
        """
        Transcribes the audio file and extracts word-level timing data.
        """
        model = self._load_model()
        segments_generator, info = model.transcribe(
            audio_path,
            language=language,
            word_timestamps=True,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500)
        )

        segments = []
        all_words = []

        for seg in segments_generator:
            words_in_seg = []
            if seg.words:
                for w in seg.words:
                    word_item = {
                        "word": w.word.strip(),
                        "start": round(w.start, 2),
                        "end": round(w.end, 2),
                        "probability": round(w.probability, 2)
                    }
                    words_in_seg.append(word_item)
                    all_words.append(word_item)

            segments.append({
                "id": seg.id,
                "start": round(seg.start, 2),
                "end": round(seg.end, 2),
                "text": seg.text.strip(),
                "words": words_in_seg
            })

        return {
            "language": info.language,
            "language_probability": round(info.language_probability, 2),
            "duration": round(info.duration, 2),
            "segments": segments,
            "words": all_words
        }
