import os
import json
from faster_whisper import WhisperModel

def transcribe_video(file_path: str, output_json_path: str = "transcript.json", model_size: str = "base"):
    """
    Transcribes a video/audio file using faster-whisper and exports a structured JSON file.
    
    Args:
        file_path (str): Path to the source media file (MP4, MP3, etc.).
        output_json_path (str): Target path where transcript.json will be saved.
        model_size (str): Model weight tier ('tiny', 'base', 'small', 'medium', 'large-v3').
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Source media file not found at: {file_path}")
        
    print(f"Initializing WhisperModel ({model_size}) on CPU/Auto...")
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    
    print(f"Transcribing: {file_path}...")
    # Relaxed speech thresholds to force detection on low-probability background audio tracks
    segments, info = model.transcribe(
        file_path, 
        beam_size=5, 
        word_timestamps=True,
        condition_on_previous_text=False,
        no_speech_threshold=0.6,
        vad_parameters=dict(min_speech_duration_ms=250)
    )
    
    print(f"Detected language: '{info.language}' with probability {info.language_probability:.2f}")
    
    transcript_data = {
        "metadata": {
            "language": info.language,
            "language_probability": info.language_probability,
            "duration": info.duration
        },
        "segments": []
    }
    
    # Process segments and structure them neatly for the Scorer module
    for segment in segments:
        segment_dict = {
            "id": segment.id,
            "start": round(segment.start, 2),
            "end": round(segment.end, 2),
            "text": segment.text.strip(),
            "words": []
        }
        
        if segment.words:
            for word in segment.words:
                segment_dict["words"].append({
                    "word": word.word.strip(),
                    "start": round(word.start, 2),
                    "end": round(word.end, 2),
                    "probability": round(word.probability, 2)
                })
                
        transcript_data["segments"].append(segment_dict)
        print(f"[{round(segment.start, 2)}s -> {round(segment.end, 2)}s]: {segment.text.strip()}")

    # Export to structured JSON
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(transcript_data, f, indent=4, ensure_ascii=False)
        
    print(f"\nSuccessfully generated: {output_json_path}")
    return transcript_data

if __name__ == "__main__":
    TEST_MEDIA = "test.mp4" 
    if os.path.exists(TEST_MEDIA):
        transcribe_video(TEST_MEDIA, "transcript.json", model_size="tiny")
    else:
        print(f"To test standalone, place a sample file named '{TEST_MEDIA}' in the project root.")