"""
effects.py

Handles:
- Zoom effect (optional)
- Caption overlay
- Face detection (Week 3 addition)
"""

import cv2
import ffmpeg


# ---------------------------
# FACE DETECTION (NEW)
# ---------------------------
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)


def detect_face_center(frame):
    """
    Detects face and returns center (cx, cy).
    If no face found → returns frame center.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(80, 80)
    )

    h, w = frame.shape[:2]

    if len(faces) == 0:
        return w // 2, h // 2

    # Take first face
    x, y, fw, fh = faces[0]

    cx = x + fw // 2
    cy = y + fh // 2

    return cx, cy


# ---------------------------
# ZOOM EFFECT (unchanged)
# ---------------------------
def apply_zoom(video_stream, zoom_factor: float = 1.08):
    return (
        video_stream
        .filter("scale", f"iw*{zoom_factor}", f"ih*{zoom_factor}")
        .filter("crop", "iw/1.08", "ih/1.08")
    )


# ---------------------------
# CAPTION OVERLAY (unchanged)
# ---------------------------
def add_caption(video_stream, text: str):
    font_path = r"C\:/Windows/Fonts/arial.ttf"

    return video_stream.filter(
        "drawtext",
        text=text.replace(":", r"\:").replace("'", r"\'"),
        fontfile=font_path,
        fontsize=48,
        fontcolor="white",
        x="(w-text_w)/2",
        y="h*0.80",
        box=1,
        boxcolor="black@0.5",
        boxborderw=10,
    )


# ---------------------------
# WATERMARK (NEW FIXED)
# ---------------------------
def add_watermark(video_stream, watermark_path, position="top_right"):
    watermark = ffmpeg.input(watermark_path)

    positions = {
        "top_left": "10:10",
        "top_right": "main_w-overlay_w-10:10",
        "bottom_left": "10:main_h-overlay_h-10",
        "bottom_right": "main_w-overlay_w-10:main_h-overlay_h-10",
    }

    pos = positions.get(position, positions["top_right"])

    x, y = pos.split(":")

    return ffmpeg.overlay(video_stream, watermark, x=x, y=y)
