import os
import json
import time
from flask import Flask, render_template, request, jsonify, url_for
from pipeline.transcriber import transcribe_video
from pipeline.scorer import ClipScorer
from pipeline.selector import select_best_segments
from pipeline.renderer import render_clip, get_crop_params

app = Flask(__name__, template_folder='templates', static_folder='static')
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(ROOT_DIR, 'uploads')
OUTPUT_FOLDER = os.path.join(ROOT_DIR, 'shorts_output')
TRANSCRIPT_PATH = os.path.join(ROOT_DIR, 'pipeline', 'transcript.json')
SCORED_TRANSCRIPT_PATH = os.path.join(ROOT_DIR, 'pipeline', 'scored_transcript.json')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(os.path.dirname(TRANSCRIPT_PATH), exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Progress Tracking
progress_data = {"progress": 0, "status": "Waiting...", "success": True}

def update_progress(progress, status, success=True):
    progress_data["progress"] = progress
    progress_data["status"]   = status
    progress_data["success"]  = success

@app.route('/api/progress')
def get_progress():
    return jsonify(progress_data)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/clips/<filename>')
def serve_clip(filename):
    """Serve video clips from shorts_output folder."""
    from flask import send_file
    file_path = os.path.join(OUTPUT_FOLDER, filename)
    if os.path.exists(file_path):
        return send_file(file_path, mimetype='video/mp4')
    return jsonify({'error': 'Clip not found'}), 404

@app.route('/api/transcribe', methods=['POST'])
def handle_transcription():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    uploaded_file = request.files['file']
    if uploaded_file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400

    file_name = os.path.basename(uploaded_file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_name)
    
    
    update_progress(0, "Starting...", True)
    update_progress(10, "Uploading video...")
    uploaded_file.save(file_path)
    transcript_path = TRANSCRIPT_PATH
    
    try:
        model_size = request.form.get('model_size', 'tiny')
        try:
            max_clips = int(request.form.get('max_clips', 3))
        except (ValueError, TypeError):
            max_clips = 3
        update_progress(20, "Extracting audio...")
        time.sleep(1)
        update_progress(40, "Transcribing video...")
        transcript_data = transcribe_video(
            file_path=file_path,
            output_json_path=transcript_path,
            model_size=model_size
        )

        segments = transcript_data.get('segments', [])
        if not segments:
            return jsonify({'error': 'No transcript segments were generated.'}), 422

        video_duration = transcript_data.get('metadata', {}).get('duration', None)
        update_progress(55, "Scoring transcript...")
        time.sleep(1)
        scored_segments = ClipScorer().score_segments(segments, video_duration=video_duration)
        with open(SCORED_TRANSCRIPT_PATH, 'w', encoding='utf-8') as scored_file:
            json.dump({'scored_segments': scored_segments}, scored_file, indent=4, ensure_ascii=False)
        update_progress(70, "Selecting best clips...")
        time.sleep(1)
        selected_segments = select_best_segments(scored_segments, max_clips=max_clips)
        
        cw, ch, cx, cy = get_crop_params(file_path)
        final_clips = []
        update_progress(85, "Rendering short videos...")
        time.sleep(1)
        for index, segment in enumerate(selected_segments, start=1):
            out_name = f'clip_{index:03d}.mp4'
            out_path = os.path.join(OUTPUT_FOLDER, out_name)

            render_clip(file_path, segment['start'], segment['end'], out_path, cw, ch, cx, cy)
            final_clips.append({
                'url': url_for('serve_clip', filename=out_name),
                'start': segment['start'],
                'end': segment['end'],
                'score': segment.get('engagement_score', 0.0)
            })
        update_progress(95, "Applying captions and effects...")
        time.sleep(1)
        update_progress(100, "Processing completed successfully")
        return jsonify({
            'message': 'Processing completed!',
            'clips': final_clips
        }), 200
    except Exception as e:
        print(f'Error: {e}')
        update_progress(progress_data["progress"], f"Failed: {str(e)}", False)
        return jsonify({'error': str(e), 'success': False}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
