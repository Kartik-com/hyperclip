"""
Dynamic 9:16 Video Compositor & Layout Generator for HyperClip.
Constructs optimized FFmpeg filter_complex graphs for:
- Solo speaker crop (9:16)
- Podcast 2-person stacked split
- Gaming stream facecam split (Game on top, webcam below)
- Letterbox Blur (Original video centered on blurred canvas)
"""

import subprocess
from pathlib import Path
from typing import Dict, Any, Tuple

class LayoutCompositor:
    def __init__(self, output_width: int = 1080, output_height: int = 1920):
        self.width = output_width
        self.height = output_height

    def build_filter_graph(self, layout_type: str, facecam_box: Tuple[float, float, float, float] = None) -> str:
        """
        Returns the FFmpeg -filter_complex string for the requested layout.
        """
        W, H = self.width, self.height

        if layout_type == "podcast_split":
            # Stack top half and bottom half
            # Top: Left half of source video (Speaker 1)
            # Bottom: Right half of source video (Speaker 2)
            top_h = H // 2
            bot_h = H - top_h
            return (
                f"[0:v]split=2[v1][v2];"
                f"[v1]crop=iw/2:ih:0:0,scale={W}:{top_h}:force_original_aspect_ratio=increase,crop={W}:{top_h}[top];"
                f"[v2]crop=iw/2:ih:iw/2:0,scale={W}:{bot_h}:force_original_aspect_ratio=increase,crop={W}:{bot_h}[bot];"
                f"[top][bot]vstack=inputs=2[v_out]"
            )

        elif layout_type == "gaming_facecam":
            # Game on top (1152px), Streamer webcam enlarged below (768px)
            game_h = int(H * 0.60)  # 1152px
            cam_h = H - game_h      # 768px

            if facecam_box:
                fx, fy, fw, fh = facecam_box
                cam_crop = f"crop=iw*{fw}:ih*{fh}:iw*{fx}:ih*{fy}"
            else:
                # Default bottom-right corner webcam
                cam_crop = "crop=iw*0.25:ih*0.25:iw*0.75:ih*0.75"

            return (
                f"[0:v]split=2[game][cam];"
                f"[game]scale={W}:{game_h}:force_original_aspect_ratio=increase,crop={W}:{game_h}[top];"
                f"[cam]{cam_crop},scale={W}:{cam_h}:force_original_aspect_ratio=increase,crop={W}:{cam_h}[bot];"
                f"[top][bot]vstack=inputs=2[v_out]"
            )

        elif layout_type == "fit_blur":
            # 16:9 original in center with blurred background filling 9:16
            return (
                f"[0:v]split=2[bg][fg];"
                f"[bg]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=25:5[bg_blurred];"
                f"[fg]scale={W}:-2:force_original_aspect_ratio=decrease[fg_scaled];"
                f"[bg_blurred][fg_scaled]overlay=(W-w)/2:(H-h)/2[v_out]"
            )

        else:
            # Default Solo: Active 9:16 Center Crop
            return (
                f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}[v_out]"
            )

    @staticmethod
    def _detect_encoder() -> Tuple[str, list]:
        """Auto-detects GPU hardware acceleration (NVENC) with CPU fallback."""
        try:
            res = subprocess.run(["ffmpeg", "-encoders"], capture_output=True, text=True, timeout=5)
            if "h264_nvenc" in res.stdout:
                return ("h264_nvenc", ["-preset", "p4", "-cq", "21"])
        except Exception:
            pass
        return ("libx264", ["-preset", "veryfast", "-crf", "19"])

    def render_cut(self, input_video: str, start: float, end: float, layout_type: str, output_path: str, subtitle_ass_path: str = None) -> str:
        """
        Executes FFmpeg to cut the clip, apply layout graph, and burn in subtitles.
        """
        duration = end - start
        vf_chain = self.build_filter_graph(layout_type)

        if subtitle_ass_path:
            # Escape path for FFmpeg filter on Windows
            clean_sub_path = str(subtitle_ass_path).replace("\\", "/").replace(":", "\\:")
            vf_chain += f";[v_out]ass='{clean_sub_path}'[final_v]"
            map_v = "[final_v]"
        else:
            map_v = "[v_out]"

        encoder, encoder_opts = self._detect_encoder()

        cmd = [
            "ffmpeg", "-y",
            "-ss", f"{start:.3f}",
            "-t", f"{duration:.3f}",
            "-i", input_video,
            "-filter_complex", vf_chain,
            "-map", map_v,
            "-map", "0:a",
            "-c:v", encoder,
            *encoder_opts,
            "-c:a", "aac",
            "-b:a", "192k",
            str(output_path)
        ]

        subprocess.run(cmd, check=True)
        return str(output_path)
