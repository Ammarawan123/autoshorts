"""
effects.py

Handles:
- Zoom effect (slow zoom-in)
- Caption overlay (text on video)
- Watermark overlay (logo/image)
"""

import ffmpeg


# ---------------------------
# ZOOM EFFECT
# ---------------------------
def apply_zoom(video_stream, zoom_factor: float = 1.08, duration: float = None):
    """
    Applies a subtle zoom-in effect using FFmpeg scale + crop animation idea.

    Args:
        video_stream: ffmpeg input video stream
        zoom_factor: final zoom level (1.0 = no zoom, 1.1 = 10% zoom)
        duration: optional (not strictly required for filter)

    Returns:
        ffmpeg video stream with zoom filter applied
    """

    # Simple zoom-in using scale filter (safe + stable approach)
    return (
        video_stream
        .filter("scale",
                f"iw*{zoom_factor}",
                f"ih*{zoom_factor}")
        .filter("crop", "iw/1.08", "ih/1.08")
    )


# ---------------------------
# CAPTION OVERLAY
# ---------------------------
def add_caption(video_stream, text: str, font_size: int = 48, font_color: str = "white", box: int = 1):
    safe_text = text.replace(":", r"\:").replace("'", r"\'")
    
    # Path ko double escape karen aur Fontconfig ko skip karne ke liye 
    # ':' ko path se alag rakhen
    font_path = r"C\:/Windows/Fonts/arial.ttf"

    return video_stream.filter(
        "drawtext",
        text=safe_text,
        fontfile=font_path,
        fontsize=font_size,
        fontcolor=font_color,
        x="(w-text_w)/2",
        y="h*0.80",
        box=box,
        boxcolor="black@0.5",
        boxborderw=10,
    )


# ---------------------------
# WATERMARK
# ---------------------------
def add_watermark(video_stream,
                  watermark_path: str,
                  position: str = "top_right"):
    """
    Overlays watermark image on video.
    """

    watermark = ffmpeg.input(watermark_path)

    # Position mapping
    positions = {
        "top_left": "(10,10)",
        "top_right": "(main_w-overlay_w-10,10)",
        "bottom_left": "(10,main_h-overlay_h-10)",
        "bottom_right": "(main_w-overlay_w-10,main_h-overlay_h-10)",
    }

    pos = positions.get(position, positions["top_right"])

    return ffmpeg.overlay(video_stream, watermark, eval=pos)
