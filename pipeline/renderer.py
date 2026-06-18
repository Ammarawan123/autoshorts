import json
import os
import logging
import ffmpeg

INPUT_VIDEO   = "input_video.mp4"
CLIPS_JSON    = "selected_clips.json"
OUTPUT_FOLDER = "output_clips"
MIN_DURATION  = 1.0

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger(__name__)


def get_crop_params(video_path: str) -> tuple:
    """Calculate 9:16 centre-crop box for the source video."""
    probe  = ffmpeg.probe(video_path)
    stream = next(s for s in probe["streams"] if s["codec_type"] == "video")
    W, H   = int(stream["width"]), int(stream["height"])

    crop_w = int(H * 9 / 16)
    crop_h = H

    # Portrait video: width already smaller than 9:16, so crop height instead
    if crop_w > W:
        crop_w, crop_h = W, int(W * 16 / 9)

    crop_w = crop_w if crop_w % 2 == 0 else crop_w - 1
    crop_h = crop_h if crop_h % 2 == 0 else crop_h - 1

    return crop_w, crop_h, (W - crop_w) // 2, (H - crop_h) // 2


def render_clip(src: str, start: float, end: float,
                out: str, cw: int, ch: int, cx: int, cy: int) -> None:
    """Cut one clip from src, crop to 9:16, scale to 1080x1920, save as H.264/AAC MP4."""
    dur = end - start

    inp   = ffmpeg.input(src, ss=start, t=dur)
    video = inp.video.filter("crop", cw, ch, cx, cy).filter("scale", 1080, 1920)
    audio = inp.audio

    (
        ffmpeg
        .output(
            video, audio, out,
            vcodec        = "libx264",
            acodec        = "aac",
            audio_bitrate = "192k",
            crf           = 23,
            preset        = "fast",
            movflags      = "+faststart"
        )
        .overwrite_output()
        .run(quiet=False, capture_stderr=True)
    )


def main() -> None:
    """Read selected_clips.json and render each segment as a vertical MP4."""
    for path in (INPUT_VIDEO, CLIPS_JSON):
        if not os.path.isfile(path):
            log.error("File not found: %s", path)
            return

    with open(CLIPS_JSON, "r", encoding="utf-8") as f:
        segments = json.load(f).get("selected_segments", [])

    if not segments:
        log.warning("No segments found in %s", CLIPS_JSON)
        return

    log.info("Loaded %d segment(s) from %s", len(segments), CLIPS_JSON)

    # Crop box is same for all clips so compute once
    cw, ch, cx, cy = get_crop_params(INPUT_VIDEO)
    log.info("9:16 crop box: %dx%d at offset (%d, %d)", cw, ch, cx, cy)

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    ok = skipped = failed = 0

    for i, seg in enumerate(segments, start=1):
        start, end = seg.get("start"), seg.get("end")

        if start is None or end is None or end <= start:
            log.warning("Segment %d invalid times - skipped.", i)
            skipped += 1
            continue

        if (end - start) < MIN_DURATION:
            log.warning("Segment %d too short - skipped.", i)
            skipped += 1
            continue

        # clip_001.mp4 format keeps files sorted
        out_path = os.path.join(OUTPUT_FOLDER, f"clip_{i:03d}.mp4")
        log.info("Rendering clip %d (%.2fs to %.2fs) ...", i, start, end)

        try:
            render_clip(INPUT_VIDEO, start, end, out_path, cw, ch, cx, cy)
            size_mb = os.path.getsize(out_path) / (1024 * 1024)
            log.info("Saved: %s (%.2f MB)", out_path, size_mb)
            ok += 1

        except ffmpeg.Error as e:
            log.error("Failed clip %d: %s",
                      i, e.stderr.decode() if e.stderr else str(e))
            failed += 1

    log.info("Done - %d rendered | %d skipped | %d failed | folder: '%s/'",
             ok, skipped, failed, OUTPUT_FOLDER)


if __name__ == "__main__":
    main()
