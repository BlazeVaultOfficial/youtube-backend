import os
import time
from flask import Flask, request, send_file, after_this_request, jsonify
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
# ඕනෑම තැනක ඇති ඔබේ Frontend වෙබ් අඩවියකට මේ සර්වර් එක සම්බන්ධ වීමට අවසර දීම (CORS)
CORS(app)

TEMP_DIR = os.path.join('/tmp', 'downloads_temp')
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

# කෙලින්ම Browser එකෙන් සබැඳියට යන විට පෙන්වන කොටස (දැන් Error එකක් එන්නේ නැත)
@app.route('/')
def home():
    return jsonify({"status": "running", "message": "YouTube Downloader Backend is working perfectly!"})

@app.route('/download', methods=['POST'])
def download_video():
    url = request.form.get('video_url')
    
    if not url:
        return jsonify({"error": "කරුණාකර නිවැරදි YouTube Link එකක් ඇතුළත් කරන්න."}), 400

    unique_id = str(int(time.time()))
    ydl_opts = {
        'outtmpl': os.path.join(TEMP_DIR, f'%(title)s_{unique_id}.%(ext)s'), 
        'format': 'best',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

        @after_this_request
        def remove_file(response):
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as error:
                app.logger.error(f"File deletion error: {error}")
            return response

        return send_file(
            file_path,
            as_attachment=True,
            download_name=os.path.basename(file_path)
        )
    
    except Exception as e:
        return jsonify({"error": f"දෝෂයක් ඇති විය: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
