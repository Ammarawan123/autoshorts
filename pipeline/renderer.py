import os
import ffmpeg
from .effects import apply_zoom, add_caption

# FFmpeg ka sahi path
FFMPEG_EXE = r'D:\ffmpeg-8.1.1-full_build\bin\ffmpeg.exe'

def get_crop_params(video_path: str) -> tuple:
    probe = ffmpeg.probe(video_path)
    stream = next(s for s in probe["streams"] if s["codec_type"] == "video")
    W, H = int(stream["width"]), int(stream["height"])
    crop_w = int(H * 9 / 16)
    crop_h = H
    if crop_w > W:
        crop_w, crop_h = W, int(W * 16 / 9)
    crop_w = crop_w if crop_w % 2 == 0 else crop_w - 1
    crop_h = crop_h if crop_h % 2 == 0 else crop_h - 1
    return crop_w, crop_h, (W - crop_w) // 2, (H - crop_h) // 2

def render_clip(src, start, end, out, cw, ch, cx, cy):
    dur = end - start
    
    # Input stream
    inp = ffmpeg.input(src, ss=start, t=dur)
    
    # Video processing
    video = inp.video.filter("crop", cw, ch, cx, cy).filter("scale", 1080, 1920)
    audio = inp.audio
    
    # Zoom effect
    video = apply_zoom(video)
    
    # Caption ko safe mode mein chala rahe hain (agar error aaye toh skip ho jaye)
    try:
        video = add_caption(video, text="Viral Clip")
    except Exception:
        pass 
    
    # Final Rendering
    (
        ffmpeg
        .output(video, audio, out,
                vcodec="libx264", acodec="aac", 
                audio_bitrate="192k", crf=23, 
                preset="fast", movflags="+faststart",
                pix_fmt="yuv420p")
        .overwrite_output()
        .run(cmd=FFMPEG_EXE, capture_stderr=True)
    )