import os
import time
from flask import Flask, render_template, request, send_file, after_this_request
import yt_dlp

app = Flask(__name__)

# Railway වැනි සර්වර් වල තාවකාලිකව වීඩියෝ සේව් කිරීමට '/tmp' ෆෝල්ඩරය භාවිත කිරීම වඩාත් සුදුසුයි
TEMP_DIR = os.path.join('/tmp', 'downloads_temp')
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download_video():
    url = request.form.get('video_url')
    
    if not url:
        return render_template('index.html', message="කරුණාකර නිවැරදි Link එකක් ඇතුළත් කරන්න.")

    # එකම නම ඇති ෆයිල් මිශ්‍ර වීම වැළැක්වීමට අද්විතීය ID එකක් (Timestamp) එකතු කරයි
    unique_id = str(int(time.time()))
    
    # yt-dlp Settings
    ydl_opts = {
        'outtmpl': os.path.join(TEMP_DIR, f'%(title)s_{unique_id}.%(ext)s'), 
        'format': 'best',  # හොඳම තත්ත්වයේ වීඩියෝව සහ ඕඩියෝව එකට ඇති format එක තෝරා ගනී
    }

    try:
        # 1. සර්වර් එක පසුබිමෙන් වීඩියෝව තාවකාලිකව බාගත කරගනී
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            # බාගත වූ ෆයිල් එකේ සැබෑ නම සහ පිහිටීම (Path) සොයාගැනීම
            file_path = ydl.prepare_filename(info)

        # 2. පරිශීලකයාට ෆයිල් එක ලැබුණු පසු සර්වර් එකේ ඉඩ ඉතිරි කරගැනීමට එම ෆයිල් එක සර්වර් එකෙන් ස්වයංක්‍රීයව මකා දැමීම
        @after_this_request
        def remove_file(response):
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as error:
                app.logger.error(f"File එක මකා දැමීමේදී දෝෂයක්: {error}")
            return response

        # 3. වීඩියෝව පරිශීලකයාගේ Browser එකට Download එකක් (Attachment) ලෙස යැවීම
        return send_file(
            file_path,
            as_attachment=True,
            download_name=os.path.basename(file_path)
        )
    
    except Exception as e:
        return render_template('index.html', message=f"දෝෂයක් ඇති විය: {str(e)}")

if __name__ == '__main__':
    # Railway එකෙන් ලබා දෙන PORT එක ගෙන ඇප් එක ක්‍රියාත්මක වේ. 
    # එය නොමැති නම් Default ලෙස 5000 port එක භාවිත කරයි.
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
