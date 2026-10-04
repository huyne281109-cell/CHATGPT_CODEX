from flask import Flask, request, send_file
import asyncio
import edge_tts
import subprocess
import os
import uuid
import io

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Server Edge-TTS cho Coconut dang hoat dong!"

async def generate_edge_tts(text, voice, output_path):
    # Khởi tạo đối tượng Communicate với giọng đọc Edge-TTS
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

@app.route('/tts', methods=['GET', 'POST'])
def tts():
    # 1. Tiếp nhận tham số từ POST (JSON) hoặc GET (Query string)
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        text = data.get('text', 'Xin chào, tôi là Coconut!')
        voice = data.get('voice', 'vi-VN-HoaiMyNeural')
    else:
        text = request.args.get('text', 'Xin chào, tôi là Coconut!')
        voice = request.args.get('voice', 'vi-VN-HoaiMyNeural')
    
    # Tạo tên file tạm ngẫu nhiên bằng UUID để tránh xung đột giữa các request
    unique_id = str(uuid.uuid4())
    mp3_file = f"/tmp/{unique_id}.mp3"
    wav_file = f"/tmp/{unique_id}.wav"
    
    try:
        # 2. Tạo file MP3 từ Edge-TTS qua SDK Python
        asyncio.run(generate_edge_tts(text, voice, mp3_file))
        
        # 3. Convert MP3 sang WAV PCM 16-bit 16kHz Mono cho ESP32
        # (16kHz giúp hạ dung lượng truyền tải, tránh giật/rè do nghẽn buffer I2S)
        subprocess.run([
            'ffmpeg', '-y',
            '-i', mp3_file,
            '-ar', '16000',
            '-ac', '1',
            '-c:a', 'pcm_s16le',
            wav_file
        ], check=True)
        
        # 4. Đọc dữ liệu file WAV vào RAM để trả về response
        with open(wav_file, 'rb') as f:
            wav_data = f.read()
            
        return send_file(
            io.BytesIO(wav_data),
            mimetype='audio/wav',
            as_attachment=False,
            download_name='speech.wav'
        )
        
    except Exception as e:
        return f"TTS Error: {str(e)}", 500
        
    finally:
        # 5. Đảm bảo xóa các file tạm sau khi đã xử lý xong
        if os.path.exists(mp3_file):
            os.remove(mp3_file)
        if os.path.exists(wav_file):
            os.remove(wav_file)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
