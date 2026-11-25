"""
HyperClip Studio Local Server - Zero Dependencies (Built-in Python HTTP)
Serves the Swiss Architectural Studio UI and executes the local video clipping pipeline.
"""

import http.server
import json
import os
import subprocess
import sys
import threading
from pathlib import Path
from urllib.parse import parse_qs, urlparse

PORT = 8484
BASE_DIR = Path(__file__).resolve().parent
PARENT_DIR = BASE_DIR.parent  # D:\video
OUTPUT_DIR = BASE_DIR / "output"
WEB_DIR = BASE_DIR / "web"

current_job = {
    "status": "idle",
    "logs": [],
    "progress": 0,
    "current_file": None,
    "results": []
}

class StudioHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Serve relative to BASE_DIR by default
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # Root and web routes serve web/index.html
        if path in ("/", "/index.html", "/web", "/web/", "/web/index.html"):
            index_file = WEB_DIR / "index.html"
            if index_file.exists():
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(index_file.read_bytes())
                return

        if path == "/api/videos":
            videos = []
            if PARENT_DIR.exists():
                for f in PARENT_DIR.glob("*.mp4"):
                    videos.append({
                        "name": f.name,
                        "path": str(f),
                        "size_mb": round(f.stat().st_size / (1024 * 1024), 1)
                    })
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(videos).encode("utf-8"))
            return

        elif path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(current_job).encode("utf-8"))
            return

        elif path == "/api/clips":
            clips = []
            if OUTPUT_DIR.exists():
                for mp4 in OUTPUT_DIR.rglob("*.mp4"):
                    clips.append({
                        "name": mp4.name,
                        "path": str(mp4),
                        "size_mb": round(mp4.stat().st_size / (1024 * 1024), 2)
                    })
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(clips).encode("utf-8"))
            return

        elif path.startswith("/media/"):
            filename = path.replace("/media/", "")
            target_file = PARENT_DIR / filename
            if target_file.exists() and target_file.suffix.lower() == ".mp4":
                self.serve_file(target_file, "video/mp4")
                return

        elif path.startswith("/rendered/"):
            filename = path.replace("/rendered/", "")
            target_file = OUTPUT_DIR / filename
            if target_file.exists():
                self.serve_file(target_file, "video/mp4")
                return

        super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/run":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            data = json.loads(body) if body else {}

            video_path = data.get("video_path", "")
            layout = data.get("layout", "auto")
            max_clips = int(data.get("max_clips", 3))

            # Resolve /media/ URLs to real local file paths
            if video_path.startswith("/media/"):
                clean_name = video_path.replace("/media/", "")
                real_file = PARENT_DIR / clean_name
                if real_file.exists():
                    video_path = str(real_file)

            if not video_path:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'{"error": "Missing video_path"}')
                return

            # Start pipeline in a worker thread
            thread = threading.Thread(target=self.run_pipeline, args=(video_path, layout, max_clips))
            thread.daemon = True
            thread.start()

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status": "started"}')
            return

        self.send_response(404)
        self.end_headers()

    def run_pipeline(self, video_path, layout, max_clips):
        global current_job
        current_job["status"] = "processing"
        current_job["logs"] = [f"🚀 Initializing HyperClip pipeline on: {video_path}"]
        current_job["current_file"] = video_path
        current_job["progress"] = 10

        try:
            python_bin = BASE_DIR / ".venv" / "Scripts" / "python.exe"
            if not python_bin.exists():
                python_bin = sys.executable

            cmd = [
                str(python_bin),
                str(BASE_DIR / "run.py"),
                str(video_path),
                "--layout", layout,
                "--max-clips", str(max_clips)
            ]

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=str(BASE_DIR),
                text=True,
                bufsize=1
            )

            for line in process.stdout:
                line_str = line.strip()
                if line_str:
                    current_job["logs"].append(line_str)
                    if "Step 2/4" in line_str:
                        current_job["progress"] = 35
                    elif "Step 3/4" in line_str:
                        current_job["progress"] = 65
                    elif "Step 4/4" in line_str:
                        current_job["progress"] = 85

            process.wait()

            if process.returncode == 0:
                current_job["status"] = "completed"
                current_job["progress"] = 100
                current_job["logs"].append("🎉 Pipeline completed successfully! Vertical clips saved.")
            else:
                current_job["status"] = "error"
                current_job["logs"].append(f"❌ Process exited with error code {process.returncode}")

        except Exception as e:
            current_job["status"] = "error"
            current_job["logs"].append(f"❌ Error: {str(e)}")

    def serve_file(self, file_path, content_type):
        try:
            stat = file_path.stat()
            file_size = stat.st_size
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(file_size))
            self.send_header("Accept-Ranges", "bytes")
            self.end_headers()
            with open(file_path, "rb") as f:
                self.copyfile(f, self.wfile)
        except Exception as e:
            self.send_response(500)
            self.end_headers()

def main():
    print("=" * 60)
    print("🚀 HyperClip Swiss Architectural Studio")
    print(f"👉 Local Web App Running at: http://localhost:{PORT}")
    print("=" * 60)
    server = http.server.ThreadingHTTPServer(("0.0.0.0", PORT), StudioHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        server.server_close()

if __name__ == "__main__":
    main()
