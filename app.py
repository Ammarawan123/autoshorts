import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import json
from flask import Flask, render_template, request, jsonify
from pipeline.transcriber import transcribe_video
from pipeline.selector import select_best_segments
from pipeline.renderer import render_clip, get_crop_params

app = Flask(__name__)

# Folders
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
OUTPUT_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'output_clips')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/transcribe', methods=['POST'])
def handle_transcription():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
        
    file = request.files['file']
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)
    
    transcript_path = os.path.join(os.path.dirname(__file__), 'transcript.json')
    
    try:
        # 1. Transcribe
        transcribe_video(file_path=file_path, output_json_path=transcript_path, model_size="tiny")
        
        # 2. Load transcript data (Checking segments structure)
        with open(transcript_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Yahan hum segments ko score ke liye map kar rahe hain (dummy score agar missing ho)
            segments = data.get("segments", [])
            for seg in segments:
                seg["engagement_score"] = seg.get("engagement_score", 1.0) 
        
        # 3. Select clips
        selected = select_best_segments(segments, max_clips=3)
        
        # 4. Render clips
        cw, ch, cx, cy = get_crop_params(file_path)
        final_clips = []
        
        for i, seg in enumerate(selected, start=1):
            out_name = f"clip_{i:03d}.mp4"
            out_path = os.path.join(OUTPUT_FOLDER, out_name)
            
            render_clip(file_path, seg['start'], seg['end'], out_path, cw, ch, cx, cy)
            final_clips.append({"url": f"/static/output_clips/{out_name}"})
            
        return jsonify({
            "message": "Processing completed!",
            "clips": final_clips
        }), 200
            
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)