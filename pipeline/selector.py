import json


def overlaps(segment1, segment2):
    """
    Returns True if two clips overlap in time.
    """

    return not (
        segment1["end"] <= segment2["start"] or
        segment2["end"] <= segment1["start"]
    )


def select_best_segments(scored_segments, max_clips=3):
    """
    Select highest-scoring non-overlapping clips.
    """

    # Sort by engagement score (highest first)
    sorted_segments = sorted(
        scored_segments,
        key=lambda x: x["engagement_score"],
        reverse=True
    )

    selected = []

    for segment in sorted_segments:

        overlap_found = False

        for chosen in selected:
            if overlaps(segment, chosen):
                overlap_found = True
                break

        if not overlap_found:
            selected.append(segment)

        if len(selected) >= max_clips:
            break

    return selected


def main():

    # Read Mariam's output
    with open("scored_transcript.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    scored_segments = data["scored_segments"]

    # Select best clips
    selected_segments = select_best_segments(
        scored_segments,
        max_clips=3
    )

    # Save output
    output = {
        "selected_segments": selected_segments
    }

    with open("selected_clips.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=4)

    print("Done!")
    print(f"Selected {len(selected_segments)} clips")


if __name__ == "__main__":
    main()
