from flask import Flask, request, Response
import subprocess
import os
import uuid

app = Flask(__name__)

SAMPLE_RATE = 24000          # PHẢI khớp EDGE_TTS_SAMPLE_RATE trong config.h
DEFAULT_VOICE = 'vi-VN-HoaiMyNeural'


@app.route('/tts', methods=['GET', 'POST'])
def tts():
    # ESP32 gửi POST JSON {"text": "...", "voice": "..."}; vẫn hỗ trợ GET để test trên trình duyệt
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        text = data.get('text', '')
        voice = data.get('voice', DEFAULT_VOICE)
    else:
        text = request.args.get('text', 'Xin chào')
        voice = request.args.get('voice', DEFAULT_VOICE)

    text = (text or '').strip()
    if not text:
        return 'text rong', 400

    mp3_file = f"/tmp/{uuid.uuid4()}.mp3"

    try:
        # 1) Edge-TTS -> MP3  (dùng --text=... để câu bắt đầu bằng dấu "-" không bị hiểu nhầm là tham số)
        subprocess.run(
            ['edge-tts', '--voice', voice, f'--text={text}', '--write-media', mp3_file],
            check=True, timeout=60, capture_output=True
        )

        # 2) FFmpeg -> PCM THÔ s16le, mono, 24 kHz, ghi ra stdout.
        #    Không có header WAV nên ESP32 không phải "đoán" độ dài header (nguyên nhân tiếng nổ/rè đầu câu).
        #    volume=0.8 chừa headroom để loa/amp không bị clip.
        ff = subprocess.run(
            ['ffmpeg', '-y', '-loglevel', 'error', '-i', mp3_file,
             '-ar', str(SAMPLE_RATE), '-ac', '1', '-af', 'volume=0.8',
             '-f', 's16le', 'pipe:1'],
            check=True, timeout=60, capture_output=True
        )
        pcm = ff.stdout
        if len(pcm) % 2:             # đảm bảo số byte chẵn (mẫu 16-bit)
            pcm = pcm[:-1]

        return Response(
            pcm,
            mimetype='application/octet-stream',
            headers={'X-Sample-Rate': str(SAMPLE_RATE), 'Content-Length': str(len(pcm))}
        )

    except subprocess.CalledProcessError as e:
        return (e.stderr or b'loi ffmpeg/edge-tts'), 500
    except Exception as e:
        return str(e), 500
    finally:
        if os.path.exists(mp3_file):
            os.remove(mp3_file)


@app.route('/', methods=['GET'])
def health():
    return 'ok'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
