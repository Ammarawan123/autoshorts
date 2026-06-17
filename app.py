import os
from flask import Flask, render_template, request, jsonify
from pipeline.transcriber import transcribe_video

app = Flask(__name__)

# Basic configurations
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    """Renders the main layout template."""
    return render_template('index.html')

@app.route('/api/transcribe', methods=['POST'])
def handle_transcription():
    """
    Endpoint that accepts a video/audio file from the UI,
    saves it locally, and processes it via your transcriber.
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file:
        # Save incoming media safely to static/uploads
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        
        # Target path for Mariam Osama's module input
        output_json_path = os.path.join(os.path.dirname(__file__), 'transcript.json')
        
        try:
            # Triggering your module logic with a light model tier for local testing
            data = transcribe_video(
                file_path=file_path, 
                output_json_path=output_json_path, 
                model_size="tiny"
            )
            return jsonify({
                "message": "Transcription completed successfully!",
                "transcript_file": output_json_path,
                "data": data
            }), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Run server locally on port 5000
    app.run(debug=True, port=5000)