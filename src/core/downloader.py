"""
Media Ingestion module for HyperClip.
Accepts a YouTube link, stream URL, or local video path.
Uses yt-dlp to extract high-quality video and audio with progress reporting.
"""

import os
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Any

class MediaDownloader:
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def ingest(self, source: str) -> Dict[str, Any]:
        """
        Ingests video from a local file path or YouTube/web URL.
        Returns paths to the source video and extracted 16kHz mono WAV for Whisper.
        """
        source_path = Path(source)
        if source_path.exists() and source_path.is_file():
            video_file = source_path
            video_id = source_path.stem
        else:
            # Download from YouTube or web link using yt-dlp
            video_id = self._extract_id_or_slug(source)
            target_template = str(self.output_dir / f"{video_id}.%(ext)s")
            
            cmd = [
                "yt-dlp",
                "--no-playlist",
                "-f", "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best",
                "--merge-output-format", "mp4",
                "-o", target_template,
                source
            ]
            
            subprocess.run(cmd, check=True)
            video_file = self.output_dir / f"{video_id}.mp4"

        # Extract 16kHz mono WAV for speech recognition
        audio_file = self.output_dir / f"{video_id}_audio.wav"
        if not audio_file.exists():
            ffmpeg_cmd = [
                "ffmpeg", "-y", "-i", str(video_file),
                "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
                str(audio_file)
            ]
            subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        return {
            "id": video_id,
            "video_path": str(video_file),
            "audio_path": str(audio_file),
        }

    def _extract_id_or_slug(self, url: str) -> str:
        # Simple slug generator from URL
        clean = "".join(c if c.isalnum() else "_" for c in url[-20:])
        return f"clip_{clean}"
