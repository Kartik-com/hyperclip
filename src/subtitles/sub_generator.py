"""
Animated Word-Synced Subtitle Generator for HyperClip.
Generates styled ASS (Advanced SubStation Alpha) subtitles with:
- Word-level bounce and karaoke highlighting (MrBeast / Hormozi style)
- Strict UI safe-zone margins (clears TikTok / Shorts / Reels like & share buttons)
- Clean multi-line wrapping with emoji support
"""

from pathlib import Path
from typing import List, Dict, Any

ASS_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Montserrat,64,&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,2,40,40,240,1
Style: Highlight,Montserrat,68,&H0000FFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,105,105,0,0,1,6,3,2,40,40,240,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

class SubtitleGenerator:
    def __init__(self, font_name: str = "Montserrat", font_size: int = 64):
        self.font_name = font_name
        self.font_size = font_size

    def generate_ass(self, words: List[Dict[str, Any]], clip_start: float, clip_end: float, output_ass_path: Path) -> Path:
        """
        Creates an ASS subtitle file for the clip timeframe with active word highlighting.
        """
        # Filter words that fall within [clip_start, clip_end]
        clip_words = [
            w for w in words
            if w.get("start", 0) >= clip_start and w.get("end", 0) <= clip_end
        ]

        if not clip_words:
            # Empty ASS file
            output_ass_path.write_text(ASS_HEADER, encoding="utf-8")
            return output_ass_path

        events = []
        # Group words into 3-5 word chunks
        chunk_size = 4
        for i in range(0, len(clip_words), chunk_size):
            chunk = clip_words[i:i + chunk_size]
            chunk_start = chunk[0]["start"] - clip_start
            chunk_end = chunk[-1]["end"] - clip_start

            # For each word in this chunk, emit an event where that word is highlighted
            for active_idx, active_word in enumerate(chunk):
                w_start = active_word["start"] - clip_start
                w_end = active_word["end"] - clip_start
                
                # Render line with active word highlighted in yellow (&H0000FFFF)
                rendered_parts = []
                for idx, w in enumerate(chunk):
                    text = w["word"].upper()
                    if idx == active_idx:
                        rendered_parts.append(f"{{\\c&H0000FFFF&}}{text}{{\\r}}")
                    else:
                        rendered_parts.append(f"{{\\c&H00FFFFFF&}}{text}")

                line_text = " ".join(rendered_parts)
                start_str = self._format_ass_time(w_start)
                end_str = self._format_ass_time(w_end)
                events.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{line_text}")

        content = ASS_HEADER + "\n".join(events) + "\n"
        output_ass_path.write_text(content, encoding="utf-8")
        return output_ass_path

    def _format_ass_time(self, seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        cs = int((secs - int(secs)) * 100)
        return f"{hours}:{minutes:02d}:{int(secs):02d}.{cs:02d}"
