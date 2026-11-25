"""
HyperClip - The Zero-Cost, Open-Source AI Video Clipping Engine.
Usage:
    python run.py "https://www.youtube.com/watch?v=VIDEO_ID"
    python run.py "D:\\video\\sample.mp4"
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

# Ensure bin directory (with ffmpeg.exe) is in PATH
ROOT_DIR = Path(__file__).resolve().parent
BIN_DIR = ROOT_DIR / "bin"
if BIN_DIR.exists():
    os.environ["PATH"] = str(BIN_DIR) + os.pathsep + os.environ.get("PATH", "")

from src.core.config import HyperConfig, OUTPUT_DIR
from src.core.downloader import MediaDownloader
from src.core.transcriber import LocalTranscriber
from src.ai.brain import UniversalBrain
from src.compositor.layout import LayoutCompositor
from src.subtitles.sub_generator import SubtitleGenerator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("hyperclip")

def clip_video(source: str, layout: str = "auto", max_clips: int = 3):
    config = HyperConfig.load()
    logger.info(f"🚀 Starting HyperClip on source: {source}")
    
    # 1. Media Ingestion
    logger.info("📥 Step 1/4: Ingesting video & extracting audio...")
    downloader = MediaDownloader(OUTPUT_DIR / "downloads")
    media = downloader.ingest(source)
    video_path = media["video_path"]
    audio_path = media["audio_path"]
    job_id = media["id"]
    job_output_dir = OUTPUT_DIR / job_id
    job_output_dir.mkdir(parents=True, exist_ok=True)
    
    # 2. Local GPU Transcription
    logger.info(f"🎙️ Step 2/4: Transcribing speech locally with Faster-Whisper ({config.whisper_model})...")
    transcriber = LocalTranscriber(model_size=config.whisper_model, device=config.transcription_device)
    transcript_data = transcriber.transcribe(audio_path)
    
    # Save transcript
    transcript_file = job_output_dir / "transcript.json"
    transcript_file.write_text(json.dumps(transcript_data, indent=2), encoding="utf-8")
    logger.info(f"✅ Transcribed {len(transcript_data['segments'])} segments ({transcript_data['duration']}s). Language: {transcript_data['language']}")
    
    # 3. Universal AI Brain Analysis
    logger.info(f"🧠 Step 3/4: Analyzing virality with AI Brain (Model: {config.llm_model})...")
    brain = UniversalBrain(
        base_url=config.llm_base_url,
        api_key=config.llm_api_key,
        model=config.llm_model
    )
    
    picks = brain.analyze_transcript(transcript_data["segments"])
    picks = picks[:max_clips]
    
    picks_file = job_output_dir / "picks.json"
    picks_file.write_text(json.dumps(picks, indent=2), encoding="utf-8")
    logger.info(f"🌟 Identified {len(picks)} viral moments!")
    
    # 4. Rendering & Layout Composition
    logger.info("✂️ Step 4/4: Generating animated subtitles and rendering 9:16 vertical clips...")
    compositor = LayoutCompositor(output_width=config.output_width, output_height=config.output_height)
    sub_gen = SubtitleGenerator()
    
    rendered_clips = []
    
    for idx, pick in enumerate(picks, 1):
        start = float(pick["start"])
        end = float(pick["end"])
        duration = end - start
        chosen_layout = layout if layout != "auto" else pick.get("recommended_layout", "solo")
        
        logger.info(f"Rendering Clip #{idx}: [{start:.1f}s - {end:.1f}s] ({duration:.1f}s) | Virality: {pick.get('virality_score')}/100 | Layout: {chosen_layout}")
        
        # Generate ASS subtitles for this clip
        ass_path = job_output_dir / f"clip_{idx}_subs.ass"
        sub_gen.generate_ass(transcript_data["words"], start, end, ass_path)
        
        # Render final vertical MP4
        clip_mp4_path = job_output_dir / f"clip_{idx}_vertical.mp4"
        compositor.render_cut(
            input_video=video_path,
            start=start,
            end=end,
            layout_type=chosen_layout,
            output_path=str(clip_mp4_path),
            subtitle_ass_path=str(ass_path)
        )
        
        rendered_clips.append({
            "clip_number": idx,
            "path": str(clip_mp4_path),
            "start": start,
            "end": end,
            "duration": round(duration, 1),
            "virality_score": pick.get("virality_score"),
            "hooks": pick.get("hook_variants", {}),
            "title": pick.get("title", ""),
            "description": pick.get("description", ""),
            "hashtags": pick.get("hashtags", [])
        })

    # Save summary report
    report_file = job_output_dir / "CLIPS_REPORT.md"
    report_lines = [
        f"# HyperClip Report: {job_id}",
        f"- Source: `{source}`",
        f"- Language: `{transcript_data['language']}`",
        f"- Total Clips Generated: `{len(rendered_clips)}`\n",
        "## Generated Clips:\n"
    ]
    
    for c in rendered_clips:
        report_lines.append(f"### Clip #{c['clip_number']} (Score: {c['virality_score']}/100)")
        report_lines.append(f"- **File**: `{c['path']}`")
        report_lines.append(f"- **Timestamps**: {c['start']}s - {c['end']}s ({c['duration']}s)")
        report_lines.append(f"- **Suggested Title**: {c['title']}")
        report_lines.append("- **A/B Hook Variations**:")
        for h_type, h_text in c['hooks'].items():
            report_lines.append(f"  - *{h_type.replace('_', ' ').title()}*: **{h_text}**")
        report_lines.append(f"- **Description**: {c['description']}")
        report_lines.append(f"- **Hashtags**: {' '.join(c['hashtags'])}\n")
        
    report_file.write_text("\n".join(report_lines), encoding="utf-8")
    
    logger.info("🎉 All clips rendered successfully!")
    logger.info(f"📁 Output directory: {job_output_dir}")
    return rendered_clips

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HyperClip - Autonomous AI Video Clipper")
    parser.add_argument("source", help="YouTube link, stream URL, or local MP4 path")
    parser.add_argument("--layout", default="auto", choices=["auto", "solo", "podcast_split", "gaming_facecam", "fit_blur"], help="Layout preset")
    parser.add_argument("--max-clips", type=int, default=3, help="Maximum number of clips to generate")
    args = parser.parse_args()
    
    clip_video(args.source, layout=args.layout, max_clips=args.max_clips)
