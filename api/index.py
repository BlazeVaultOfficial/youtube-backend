from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return "Toolz Backend Running ✅"

@app.route('/api/info', methods=['POST', 'GET'])
def info():
    try:
        url = request.json.get('url') if request.json else request.args.get('url')
        opts = {'quiet': True, 'skip_download': True}
        with yt_dlp.YoutubeDL(opts) as ydl:
            meta = ydl.extract_info(url, download=False)
            formats = []
            seen = set()
            for f in meta.get('formats', []):
                h = f.get('height')
                if h and f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                    q = f"{h}p"
                    if q not in seen:
                        seen.add(q)
                        formats.append({"format_id": f['format_id'], "quality": q, "ext": f['ext']})
            formats.sort(key=lambda x: int(x['quality'][:-1]), reverse=True)
            formats.append({"format_id": "bestaudio", "quality": "MP3 Audio", "ext": "mp3"})
            return jsonify({"status": "success", "title": meta.get('title'), "thumbnail": meta.get('thumbnail'), "formats": formats})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Vercel needs this
app = app
