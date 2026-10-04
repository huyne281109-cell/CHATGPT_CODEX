from flask import Flask, request, send_file
import subprocess
import os
import uuid
import io

app = Flask(__name__)

@app.route('/tts', methods=['GET'])
def tts():
    # Nhận text từ ESP32 gửi lên
    text = request.args.get('text', 'Xin chào')
    voice = request.args.get('voice', 'vi-VN-HoaiMyNeural')
    
    # Tạo ID ngẫu nhiên để không bị trùng file nếu có nhiều request
    unique_id = str(uuid.uuid4())
    mp3_file = f"/tmp/{unique_id}.mp3"
    wav_file = f"/tmp/{unique_id}.wav"
    
    try:
        # Tải file MP3 từ Edge-TTS
        subprocess.run(['edge-tts', '--voice', voice, '--text', text, '--write-media', mp3_file], check=True)
        
        # Dùng FFmpeg ép về đúng chuẩn I2S cho ESP32: 24kHz, Mono, 16-bit PCM
        subprocess.run(['ffmpeg', '-y', '-i', mp3_file, '-ar', '24000', '-ac', '1', '-c:a', 'pcm_s16le', wav_file], check=True)
        
        # Đọc dữ liệu âm thanh vào RAM
        with open(wav_file, 'rb') as f:
            wav_data = f.read()
            
        # Gửi file trả về cho ESP32
        return send_file(
            io.BytesIO(wav_data),
            mimetype='audio/wav'
        )
        
    except Exception as e:
        return str(e), 500
        
    finally:
        # Xóa file tạm để dọn dẹp máy chủ
        if os.path.exists(mp3_file): os.remove(mp3_file)
        if os.path.exists(wav_file): os.remove(wav_file)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)