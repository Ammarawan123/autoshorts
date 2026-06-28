import os
import json
import time
from flask import Flask, render_template, request, jsonify, url_for
from pipeline.transcriber import transcribe_video
from pipeline.scorer import SemanticScorer
from pipeline.selector import select_best_segments
from pipeline.renderer import render_clip, get_crop_params
import subprocess

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

ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv', 'webm'}

MAX_FILE_SIZE_MB = 500

progress_data = {"progress": 0, "status": "Waiting...", "success": True}

# Helper Functions 
def update_progress(progress, status, success=True):
    """Update the global progress tracker."""
    progress_data["progress"] = progress
    progress_data["status"]   = status
    progress_data["success"]  = success

def check_ffmpeg():
    """
    Cross-platform FFmpeg detection.
    Works on Windows, Linux and macOS.
    """

    import shutil
    import os
    import subprocess

    ffmpeg = shutil.which("ffmpeg")

    if ffmpeg is None:
        possible_paths = [
            r"C:\ffmpeg\bin\ffmpeg.exe",
            r"C:\ffmpeg-8.1.2-essentials_build\bin\ffmpeg.exe",
            r"C:\ffmpeg-8.1.2-essentials_build\ffmpeg-8.1.2-essentials_build\bin\ffmpeg.exe",
        ]

        for path in possible_paths:
            if os.path.exists(path):
                ffmpeg = path
                break

    if ffmpeg is None:
        return False

    try:
        subprocess.run(
            [ffmpeg, "-version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return True
    except Exception:
        return False

# Routes 
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/progress')
def get_progress():
    """Return current processing progress to the frontend."""
    return jsonify(progress_data)


@app.route('/clips/<filename>')
def serve_clip(filename):
    """Serve a rendered video clip from the output folder."""
    from flask import send_file
    file_path = os.path.join(OUTPUT_FOLDER, filename)
    if os.path.exists(file_path):
        return send_file(file_path, mimetype='video/mp4')
    return jsonify({'success': False, 'message': 'Clip not found.'}), 404

# Error Handlers 
@app.errorhandler(404)
def not_found(e):
    """Handle 404 Not Found errors."""
    return jsonify({"success": False, "message": "Resource not found."}), 404


@app.errorhandler(500)
def server_error(e):
    """Handle 500 Internal Server errors."""
    return jsonify({"success": False, "message": "Internal server error."}), 500


@app.errorhandler(413)
def file_too_large(e):
    """Handle file size exceeded errors."""
    return jsonify({"success": False, "message": "File too large. Maximum 500MB."}), 413

# Main API 
@app.route('/api/transcribe', methods=['POST'])
def handle_transcription():
    """
    Main endpoint — receives video, runs full pipeline:
    transcribe → score → select → render → return clips.
    """

    if not check_ffmpeg():
        return jsonify({"success": False, "message": "FFmpeg is not installed on this server."}), 500

    if 'file' not in request.files:
        return jsonify({"success": False, "message": "No video uploaded."}), 400

    uploaded_file = request.files['file']

    if uploaded_file.filename == '':
        return jsonify({"success": False, "message": "No file selected."}), 400

    filename = uploaded_file.filename.strip()
    if '.' not in filename:
        return jsonify({"success": False, "message": "Invalid file. Please upload mp4, mov, avi, mkv or webm."}), 400
    ext = filename.rsplit('.', 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({"success": False, "message": f"Format '.{ext}' not supported. Please upload mp4, mov, avi, mkv or webm."}), 400

    file_name = os.path.basename(uploaded_file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_name)

    update_progress(0, "Starting...", True)
    update_progress(10, "Uploading video...")
    uploaded_file.save(file_path)

    size_mb = os.path.getsize(file_path) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        os.remove(file_path)
        return jsonify({"success": False, "message": f"File too large ({size_mb:.1f}MB). Maximum allowed size is {MAX_FILE_SIZE_MB}MB."}), 400

    transcript_path = TRANSCRIPT_PATH

    model_size = request.form.get('model_size', 'tiny')
    try:
        max_clips = int(request.form.get('max_clips', 3))
    except (ValueError, TypeError):
        max_clips = 3

    try:

        update_progress(20, "Extracting audio...")
        time.sleep(1)
        update_progress(40, "Transcribing video...")

        try:
            transcript_data = transcribe_video(
                file_path=file_path,
                output_json_path=TRANSCRIPT_PATH,
                model_size=model_size
            )
        except FileNotFoundError as e:
            update_progress(40, "Video file not found.", False)
            return jsonify({"success": False, "message": f"Video file missing: {e}"}), 404
        except RuntimeError as e:
            update_progress(40, "Transcription failed.", False)
            return jsonify({"success": False, "message": f"Transcription error: {e}"}), 500
        except Exception as e:
            print(f"[ERROR] Transcriber: {e}")
            update_progress(40, "Transcription failed.", False)
            return jsonify({"success": False, "message": "Transcription failed. Please ensure video has clear audio."}), 500

        
        
        segments = transcript_data.get('segments', [])
        if not segments:
            update_progress(progress_data["progress"], "No speech detected in video.", False)
            return jsonify({"success": False, "message": "No speech detected. Please upload a video with clear audio."}), 422

        video_duration = transcript_data.get('metadata', {}).get('duration', None)

        update_progress(55, "Scoring transcript...")
        time.sleep(1)

        try:
            scorer = SemanticScorer()
            scored_segments = [
                {**seg, 'engagement_score': round(scorer.get_semantic_score(seg['text']), 2)}
                for seg in segments
]
        except Exception:
            update_progress(55, "Scoring failed.", False)
            return jsonify({"success": False, "message": "Clip scoring failed. Please try again."}), 500

        with open(SCORED_TRANSCRIPT_PATH, 'w', encoding='utf-8') as scored_file:
            json.dump({'scored_segments': scored_segments}, scored_file, indent=4, ensure_ascii=False)

        update_progress(70, "Selecting best clips...")
        time.sleep(1)

        try:
            selected_segments = select_best_segments(scored_segments, max_clips=max_clips)
        except Exception:
            update_progress(70, "Clip selection failed.", False)
            return jsonify({"success": False, "message": "Clip selection failed. Please try again."}), 500

        if not selected_segments:
            update_progress(70, "No clips found.", False)
            return jsonify({"success": False, "message": "No suitable clips found in this video."}), 422
        
        cw, ch = get_crop_params(file_path)
        final_clips = []
        update_progress(85, "Rendering short videos...")
        time.sleep(1)

        for index, segment in enumerate(selected_segments, start=1):
            out_name = f'clip_{index:03d}.mp4'
            out_path = os.path.join(OUTPUT_FOLDER, out_name)

            try:
                render_clip(file_path, segment['start'], segment['end'], out_path, cw, ch)
            except Exception:
                update_progress(85, f"Rendering failed for clip {index}.", False)
                return jsonify({"success": False, "message": f"Rendering failed for clip {index}. Please try again."}), 500

            if not os.path.exists(out_path):
                update_progress(85, f"Clip {index} not generated.", False)
                return jsonify({"success": False, "message": f"Clip {index} was not generated."}), 500

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
            "success": True,
            "message": "Processing completed!",
            "clips": final_clips
        }), 200

    except Exception as e:
        print(f'Error: {e}')
        update_progress(progress_data["progress"], "Something went wrong. Please try again.", False)
        return jsonify({"success": False, "message": "An unexpected error occurred. Please try again."}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
