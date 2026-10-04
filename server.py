from flask import Flask, request, send_file
import subprocess
import os
import uuid
import io

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Server Edge-TTS cho Coconut dang hoat dong!"

@app.route('/tts', methods=['GET', 'POST'])
def tts():
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        text = data.get('text', 'Xin chào')
        voice = data.get('voice', 'vi-VN-HoaiMyNeural')
    else:
        text = request.args.get('text', 'Xin chào')
        voice = request.args.get('voice', 'vi-VN-HoaiMyNeural')
    
    unique_id = str(uuid.uuid4())
    mp3_file = f"/tmp/{unique_id}.mp3"
    wav_file = f"/tmp/{unique_id}.wav"
    
    try:
        subprocess.run(['edge-tts', '--voice', voice, '--text', text, '--write-media', mp3_file], check=True)
        subprocess.run(['ffmpeg', '-y', '-i', mp3_file, '-ar', '24000', '-ac', '1', '-c:a', 'pcm_s16le', wav_file], check=True)
        
        with open(wav_file, 'rb') as f:
            wav_data = f.read()
            
        return send_file(io.BytesIO(wav_data), mimetype='audio/wav')
        
    except Exception as e:
        return str(e), 500
        
    finally:
        if os.path.exists(mp3_file): os.remove(mp3_file)
        if os.path.exists(wav_file): os.remove(wav_file)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
