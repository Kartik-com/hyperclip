<p align="center">
  <h1 align="center">⚡ HyperClip</h1>
  <p align="center"><strong>The 100% Free, Local-First AI Video Clipper with $0 Cloud Bills.</strong></p>
  <p align="center">Turn long-form videos & live streams into viral, ready-to-post 9:16 Shorts with animated subtitles, smart framing, and data-ranked hooks.</p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge" alt="MIT License">
  <img src="https://img.shields.io/badge/Hardware-GPU_Accelerated-76B900?style=for-the-badge&logo=nvidia" alt="GPU Accelerated">
  <img src="https://img.shields.io/badge/Platforms-Windows_|_Linux_|_macOS-lightgrey?style=for-the-badge" alt="Cross Platform">
  <img src="https://img.shields.io/badge/Zero_Cost-100%25_Free-brightgreen?style=for-the-badge" alt="Zero Cost">
</p>

---

## 🔥 Why HyperClip?

Commercial tools like **OpusClip** charge **$29–$49/month**, limit you to 60–150 minutes, and watermark your exports. Existing open-source alternatives require complex Docker containers and paid cloud API tokens.

**HyperClip gives you the full studio pipeline with ZERO cloud subscriptions:**
- **$0 Running Cost**: Runs local `faster-whisper` on your NVIDIA GPU (or CPU) + connects to **any free LLM** (Google Gemini free tier, FreeLLMAPI, or local Ollama).
- **Native 1-Click Windows Support**: No Docker required. Run directly on your PC.
- **Smart Dynamic Layouts**:
  - **Solo Speaker Crop (9:16)**
  - **Two-Person Podcast Stacked Split** (Host on top, Guest below, subtitles on seam)
  - **Gaming Streamer Split** (Gameplay on top, Webcam below)
  - **Letterbox Fit Blur**
- **Data-Ranked Viral Hooks**: Tested against 3,480+ viral shorts. Every clip generates **3 A/B hook variants** (Number Promise 2.46x, Shock Fact 1.68x, Curiosity Gap 1.48x).
- **Hindi & Hinglish Ready**: Accurately recognizes and captions bilingual Hinglish speech.

---

## 📊 Comparison

| Feature | OpusClip | CapCut Pro | **HyperClip** |
| :--- | :---: | :---: | :---: |
| **Monthly Subscription** | $29–$49/mo | $12/mo | **$0 (Free & Open Source)** |
| **Video Processing Limit**| Metered (150 mins) | Metered | **Unlimited** |
| **Watermark** | Yes (Free plan) | Yes | **None** |
| **Hardware Acceleration**| Cloud servers | Cloud / Basic | **Local GPU / CPU Acceleration** |
| **AI LLM Providers** | Proprietary | Proprietary | **Universal (FreeLLMAPI, Gemini, Ollama, OpenAI)** |
| **Gaming Webcam Split** | ❌ Basic | Manual | **✅ Automatic Game + Cam Split** |
| **Dual Podcast Split** | Basic | Manual | **✅ Automatic 2-Person Stack** |
| **A/B Hook Variations** | 1 output | 1 output | **✅ 3 Data-Ranked Variations** |

---

## 🚀 Quick Start

### 1. Installation (Windows)
Double-click `install.bat` or run:
```powershell
git clone https://github.com/Kartik-com/hyperclip.git
cd hyperclip
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### 2. Configure Your Free AI Key
Copy `.env.example` to `.env`:
```env
# Point to your custom FreeLLMAPI or Gemini free key:
LLM_BASE_URL=http://localhost:8080/v1
LLM_API_KEY=your_key
LLM_MODEL=gpt-4o-mini
```

### 3. Run Your First Clip!
```powershell
python run.py "https://www.youtube.com/watch?v=VIDEO_ID"
```
Or for a local file:
```powershell
python run.py "D:\video\sample.mp4" --layout auto --max-clips 3
```

Finished 9:16 vertical clips, animated subtitles, titles, descriptions, and hashtags will be saved directly into `output/`!

---

## 🎨 Supported Layouts

```
[ Solo Active Crop ]       [ Podcast 2-Person ]       [ Gaming Streamer ]
  ┌──────────────┐           ┌──────────────┐           ┌──────────────┐
  │              │           │    Host      │           │   GAMEPLAY   │
  │    ( 👤 )    │           ├──────────────┤           ├──────────────┤
  │   Speaker    │           │  "CAPTIONS"  │           │  "CAPTIONS"  │
  │              │           ├──────────────┤           ├──────────────┤
  │  "CAPTIONS"  │           │    Guest     │           │   Webcam 🎙️  │
  └──────────────┘           └──────────────┘           └──────────────┘
```

---

## 📄 License
MIT License. Free for individual creators, agencies, and developers.
