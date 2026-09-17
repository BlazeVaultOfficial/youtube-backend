from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import yt_dlp
import os
import tempfile

app = Flask(__name__)
CORS(app)

# =========================
# SETTINGS
# =========================

DENO_PATH = r"C:\Users\w\.deno\bin\deno.exe"


def ytdlp_options():
    return {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,

        # JavaScript runtime
        "js_runtimes": {
            "deno": {
                "path": DENO_PATH
            }
        }
    }


# =========================
# HOME
# =========================

@app.route("/")
def home():
    return jsonify({
        "status": "success",
        "message": "Toolz YouTube Downloader API is running!"
    })


# =========================
# API TEST
# =========================

@app.route("/api/test")
def test():
    return jsonify({
        "status": "success",
        "message": "API connection is working!"
    })


# =========================
# GET VIDEO INFORMATION
# =========================

@app.route("/api/info", methods=["POST"])
def video_info():

    data = request.get_json(silent=True)

    if not data or "url" not in data:
        return jsonify({
            "status": "error",
            "message": "YouTube URL is required"
        }), 400

    url = data["url"].strip()

    if not url:
        return jsonify({
            "status": "error",
            "message": "YouTube URL is empty"
        }), 400

    try:

        options = ytdlp_options()

        with yt_dlp.YoutubeDL(options) as ydl:

            info = ydl.extract_info(
                url,
                download=False
            )

        # =========================
        # BUILD AVAILABLE QUALITIES
        # =========================

        quality_map = {}

        for fmt in info.get("formats", []):

            height = fmt.get("height")
            ext = fmt.get("ext")
            format_id = fmt.get("format_id")

            if not height or not format_id:
                continue

            # Only keep useful video formats
            if height < 144:
                continue

            quality = f"{height}p"

            # Prefer MP4
            if quality not in quality_map or ext == "mp4":

                quality_map[quality] = {
                    "quality": quality,
                    "height": height,
                    "format": ext,
                    "format_id": format_id
                }

        # Sort highest to lowest
        formats = sorted(
            quality_map.values(),
            key=lambda x: x["height"],
            reverse=True
        )

        # Audio option
        formats.append({
            "quality": "audio",
            "height": None,
            "format": "audio",
            "format_id": "bestaudio"
        })

        return jsonify({
            "status": "success",
            "title": info.get("title"),
            "thumbnail": info.get("thumbnail"),
            "duration": info.get("duration"),
            "formats": formats
        })

    except Exception as e:

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# =========================
# DOWNLOAD
# =========================

@app.route("/api/download", methods=["POST"])
def download():

    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "status": "error",
            "message": "Request data is required"
        }), 400

    url = data.get("url", "").strip()
    quality = data.get("quality", "").strip()

    if not url:
        return jsonify({
            "status": "error",
            "message": "YouTube URL is required"
        }), 400

    if not quality:
        return jsonify({
            "status": "error",
            "message": "Quality is required"
        }), 400

    try:

        download_dir = os.path.join(
            tempfile.gettempdir(),
            "toolz_youtube"
        )

        os.makedirs(download_dir, exist_ok=True)

        options = {
            "quiet": True,
            "no_warnings": True,

            "js_runtimes": {
                "deno": {
                    "path": DENO_PATH
                }
            },

            "outtmpl": os.path.join(
                download_dir,
                "%(title)s.%(ext)s"
            ),

            # Keep downloaded files
            "noplaylist": True
        }

        # =========================
        # QUALITY
        # =========================

        if quality == "audio":

            options.update({
                "format": "bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192"
                }]
            })

        else:

            height = int(
                quality.replace("p", "")
            )

            # Prefer MP4 video + M4A audio.
            # Fall back to a combined format if available.
            options["format"] = (
                f"bestvideo[height<={height}][ext=mp4]"
                f"+bestaudio[ext=m4a]/"
                f"best[height<={height}]"
            )

            options["merge_output_format"] = "mp4"

        # =========================
        # DOWNLOAD
        # =========================

        with yt_dlp.YoutubeDL(options) as ydl:

            info = ydl.extract_info(
                url,
                download=True
            )

            filename = ydl.prepare_filename(info)

            # MP3 output filename
            if quality == "audio":

                base, _ = os.path.splitext(filename)
                filename = base + ".mp3"

            # Merged MP4 output
            else:

                base, _ = os.path.splitext(filename)
                filename = base + ".mp4"

        if not os.path.exists(filename):

            return jsonify({
                "status": "error",
                "message": "Downloaded file was not found."
            }), 500

        return send_file(
            filename,
            as_attachment=True,
            download_name=os.path.basename(filename)
        )

    except Exception as e:

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# =========================
# START SERVER
# =========================

if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port
    )
