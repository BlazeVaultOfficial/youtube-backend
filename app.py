from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import os
app = Flask(__name__)
CORS(app)
@app.route('/')
def home():
    return "Toolz Backend Running! ✅"
@app.route('/api/info', methods=['POST'])
def get_info():
    try:
        data = request.get_json()
        url = data.get('url')
        if not url:
            return jsonify({"status": "error", "message": "URL is required"}), 400
        ydl_opts = {'quiet': True, 'no_warnings': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = []
            for f in info.get('formats', []):
                if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                    h = f.get('height')
                    if h:
                        formats.append({"format_id": f['format_id'],"quality": f"{h}p","format": f['ext']})
            seen=set()
            uniq=[]
            for fmt in formats:
                if fmt['quality'] not in seen:
                    seen.add(fmt['quality'])
                    uniq.append(fmt)
            uniq.sort(key=lambda x: int(x['quality'].replace('p','')), reverse=True)
            uniq.append({"format_id": "bestaudio", "quality": "Audio Only", "format": "mp3"})
            return jsonify({"status": "success","title": info.get('title'),"thumbnail": info.get('thumbnail'),"formats": uniq})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)