"""
Universal AI Brain for HyperClip.
Supports any OpenAI-compatible API, custom FreeLLMAPI, Ollama, Gemini, Groq, or OpenAI.
Evaluates transcripts, finds viral moments, and writes data-ranked A/B hook variants.
"""

import json
import logging
import os
import re
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional

logger = logging.getLogger("hyperclip.ai")

SYSTEM_PROMPT = """You are an elite short-form video editor and viral content strategist for YouTube Shorts, TikTok, and Instagram Reels.
Your task is to analyze video transcripts, identify the top 3-5 most engaging moments, and package them into viral 9:16 clips.

RULES FOR SELECTING MOMENTS:
1. Strong Cold Open: Must open on a compelling statement, question, reaction, or action beat within the first 2 seconds. Never start on boring filler ("Um", "So guys", "Yeah").
2. Standalone Narrative: The clip must make complete sense on its own without needing the rest of the 2-hour video.
3. Payoff Delivery: The clip MUST deliver on the premise before the end (reveal, punchline, reaction, or outcome).
4. Duration: Ideal clip duration is 25 to 55 seconds (never shorter than 15s, never longer than 60s).

VIRAL HOOK MATRIX (Every clip MUST generate 3 distinct hook variations based on viral data):
- Hook A (Number Promise - 2.46x benchmark): Expresses a count or list format (e.g. "3 THINGS HE DIDN'T EXPECT...", "4 REASONS WHY...")
- Hook B (Shock Fact / Bold Claim - 1.68x benchmark): Intense statement of fact or disbelief (e.g. "THIS ACTUALLY HAPPENED...", "NOBODY REALIZED...")
- Hook C (Curiosity Gap / Question - 1.48x benchmark): Sets up a mystery that viewer must watch to resolve (e.g. "Why did he stop right here?", "Watch his face at the end...")

LAYOUT RECOMMENDATION:
- "solo": Single speaker talking head.
- "podcast_split": Two or more people interacting, interviewing, or laughing.
- "gaming_facecam": Streamer webcam overlay on top of gameplay.

OUTPUT FORMAT:
Return ONLY a valid JSON array of objects with no markdown code blocks, structured as:
[
  {
    "id": 1,
    "start": 124.5,
    "end": 168.2,
    "virality_score": 88,
    "reasoning": "High-energy reaction with a clear twist ending.",
    "hook_variants": {
      "number_promise": "3 REASONS WHY THIS HAPPENED...",
      "shock_fact": "HE COULD NOT BELIEVE THIS...",
      "curiosity_gap": "Wait until you see what happened next..."
    },
    "recommended_layout": "solo",
    "title": "Shocking Moment on Stream",
    "description": "You won't believe how this turned out! #shorts #viral #trending",
    "hashtags": ["#shorts", "#viral", "#gaming", "#trending"]
  }
]
"""

class UniversalBrain:
    def __init__(self, base_url: str = "", api_key: str = "", model: str = "gpt-4o-mini"):
        # Auto-detect or normalize base_url
        self.base_url = (base_url or os.getenv("LLM_BASE_URL", "")).rstrip("/")
        self.api_key = api_key or os.getenv("LLM_API_KEY", "") or os.getenv("OPENAI_API_KEY", "") or "free"
        self.model = model or os.getenv("LLM_MODEL", "gpt-4o-mini")
        
        # If no custom URL is given, default to standard OpenAI endpoint
        if not self.base_url:
            self.base_url = "https://api.openai.com/v1"
        elif not self.base_url.endswith("/v1"):
            self.base_url = f"{self.base_url}/v1"

    def analyze_transcript(self, transcript_segments: List[Dict[str, Any]], audio_events: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """
        Sends formatted transcript to the LLM and parses the viral picks.
        Falls back to local heuristic analysis if LLM is unreachable.
        """
        if not transcript_segments:
            return []

        # Attempt AI Brain LLM evaluation first
        try:
            formatted_text = self._format_transcript_for_prompt(transcript_segments, audio_events)
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Analyze this transcript and find the top viral clips:\n\n{formatted_text}"}
            ]
            raw_response = self._call_llm(messages)
            picks = self._clean_and_parse_json(raw_response)
            if picks and len(picks) > 0:
                logger.info(f"AI Brain successfully identified {len(picks)} clips via LLM.")
                return picks
        except Exception as e:
            logger.warning(f"AI Brain endpoint unavailable ({e}). Smoothly activating local heuristic hook engine.")

        # Local Zero-Cost Heuristic Fallback
        return self._heuristic_fallback(transcript_segments)

    def _heuristic_fallback(self, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Offline algorithm: evaluates transcript cadence, speech density, and punctuation beats
        to pinpoint the highest-retention 30-55 second clips without an active LLM key.
        """
        logger.info("Executing local heuristic moment analysis on transcript...")
        
        candidates = []
        n = len(segments)
        i = 0
        
        while i < n:
            start_seg = segments[i]
            clip_start = float(start_seg.get("start", 0))
            clip_text_parts = [start_seg.get("text", "").strip()]
            
            j = i + 1
            while j < n:
                curr_seg = segments[j]
                curr_end = float(curr_seg.get("end", 0))
                duration = curr_end - clip_start
                
                if duration > 55:
                    break
                    
                clip_text_parts.append(curr_seg.get("text", "").strip())
                
                if duration >= 25:
                    # Valid candidate window
                    full_text = " ".join(clip_text_parts)
                    words = full_text.split()
                    wpm = (len(words) / max(duration, 1)) * 60
                    
                    # Score based on speech density, exclamation/question beats, and ideal 35-45s length
                    score = min(95, int(60 + min(wpm / 10, 25) + full_text.count("?") * 3 + full_text.count("!") * 3))
                    
                    candidates.append({
                        "start": round(clip_start, 1),
                        "end": round(curr_end, 1),
                        "duration": round(duration, 1),
                        "virality_score": score,
                        "text": full_text
                    })
                j += 1
                
            i += max(1, (j - i) // 2)

        if not candidates:
            # Fallback for very short video: take entire span
            total_end = float(segments[-1].get("end", 30))
            candidates = [{
                "start": 0.0,
                "end": total_end,
                "duration": total_end,
                "virality_score": 85,
                "text": " ".join(s.get("text", "") for s in segments)
            }]

        # Sort by virality score and pick non-overlapping moments
        candidates.sort(key=lambda x: x["virality_score"], reverse=True)
        selected = []
        
        for cand in candidates:
            overlap = False
            for sel in selected:
                if not (cand["end"] <= sel["start"] or cand["start"] >= sel["end"]):
                    overlap = True
                    break
            if not overlap:
                selected.append(cand)
            if len(selected) >= 3:
                break

        # Format output matching the AI Brain JSON schema
        formatted_picks = []
        for idx, pick in enumerate(selected, 1):
            sample_words = [w for w in pick["text"].split() if len(w) > 3][:6]
            teaser = " ".join(sample_words).upper() if sample_words else "KEY MOMENT"
            
            formatted_picks.append({
                "id": idx,
                "start": pick["start"],
                "end": pick["end"],
                "virality_score": pick["virality_score"],
                "reasoning": "High-density speech segment with continuous narrative momentum.",
                "hook_variants": {
                    "number_promise": f"3 REASONS WHY {teaser}...",
                    "shock_fact": f"THE HIDDEN TRUTH ABOUT {teaser}...",
                    "curiosity_gap": f"Notice what happens right after this moment..."
                },
                "recommended_layout": "solo",
                "title": f"The Moment {teaser.title()}",
                "description": f"High retention highlight clip generated by HyperClip. #shorts #viral #trending",
                "hashtags": ["#shorts", "#viral", "#trending", "#hyperclip"]
            })

        return formatted_picks

    def _call_llm(self, messages: List[Dict[str, str]]) -> str:
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.4,
        }
        
        data = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": "HyperClip/1.0"
        }
        
        req = urllib.request.Request(url, data=data, headers=headers)
        
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            err_msg = e.read().decode("utf-8", errors="ignore")
            logger.error(f"HTTP Error {e.code} calling {url}: {err_msg}")
            raise RuntimeError(f"LLM API Error ({e.code}): {err_msg}")
        except Exception as e:
            logger.error(f"Network error calling {url}: {e}")
            raise

    def _format_transcript_for_prompt(self, segments: List[Dict[str, Any]], audio_events: Optional[List[Dict[str, Any]]] = None) -> str:
        lines = []
        for s in segments:
            start_m, start_s = divmod(int(s.get("start", 0)), 60)
            end_m, end_s = divmod(int(s.get("end", 0)), 60)
            speaker = f"[{s.get('speaker', 'Speaker')}]: " if s.get("speaker") else ""
            lines.append(f"[{start_m:02d}:{start_s:02d} - {end_m:02d}:{end_s:02d}] {speaker}{s.get('text', '').strip()}")
        return "\n".join(lines)

    def _clean_and_parse_json(self, raw_text: str) -> List[Dict[str, Any]]:
        cleaned = raw_text.strip()
        # Remove markdown code fences if present
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            # Fallback regex extraction of JSON array
            match = re.search(r"\[\s*\{.*\}\s*\]", cleaned, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            logger.error(f"Failed to parse LLM JSON: {cleaned}")
            raise RuntimeError(f"LLM did not return valid JSON: {e}")
