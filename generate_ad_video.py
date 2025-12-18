import json
import base64
import subprocess
import textwrap
import uuid
from pathlib import Path

from openai import OpenAI

# ---------------- CONFIG ----------------
MODEL_TEXT = "gpt-4o-mini"

# Use DALL·E 3 to avoid org-verification gating for gpt-image-1
MODEL_IMAGE = "dall-e-3"

MODEL_TTS = "gpt-4o-mini-tts"
VOICE = "alloy"

OUT_W, OUT_H = 1080, 1920
FPS = 30

client = OpenAI()


def run(cmd: list[str], cwd: str | None = None):
    subprocess.run(cmd, check=True, cwd=cwd)


def safe_drawtext(s: str) -> str:
    """
    Escape text for ffmpeg drawtext.
    """
    s = s.replace("\\", "\\\\")
    s = s.replace(":", "\\:")
    s = s.replace("'", "\\'")
    s = s.replace("\n", " ")
    return s.strip()


def make_scenes(product_desc: str, platform: str = "TikTok", tone: str = "Bold") -> dict:
    """
    Ask the model for JSON. Parse it ourselves. Then enforce exactly 5 scenes
    by padding/trimming so the pipeline never fails.
    """
    prompt = f"""
You are a performance marketer.

Create ONE short vertical video ad for {platform}.

Rules:
- Total length 18–25 seconds
- Exactly 5 scenes:
  1. Hook
  2–4. Benefits
  5. CTA
- Return VALID JSON ONLY (no markdown, no explanation)

JSON format:
{{
  "headline": "string",
  "cta": "string",
  "scenes": [
    {{
      "seconds": 4,
      "caption": "short caption (<= 9 words)",
      "narration": "one sentence narration",
      "visual_prompt": "detailed visual description, no logos, no text in image"
    }}
  ]
}}

Tone: {tone}

Product description:
{product_desc}
""".strip()

    resp = client.responses.create(
        model=MODEL_TEXT,
        input=prompt
    )

    raw = resp.output_text.strip()

    try:
        ad = json.loads(raw)
    except Exception:
        print("\n❌ Model did not return valid JSON.\n--- RAW OUTPUT START ---")
        print(raw)
        print("--- RAW OUTPUT END ---\n")
        raise

    # Basic validation
    if not isinstance(ad, dict):
        raise ValueError("Expected JSON object.")
    if "scenes" not in ad or not isinstance(ad["scenes"], list):
        raise ValueError("Expected JSON with 'scenes' array.")

    # Enforce exactly 5 scenes: pad or trim
    scenes = ad["scenes"]

    # If fewer than 5 scenes, pad with a CTA-like scene(s)
    if len(scenes) < 5:
        fallback_visual = "A clean product hero shot on a studio background, modern lighting, shallow depth of field."
        while len(scenes) < 5:
            scenes.append({
                "seconds": 4,
                "caption": "Order now",
                "narration": "Order now and experience it today.",
                "visual_prompt": fallback_visual
            })

    # If more than 5 scenes, trim
    if len(scenes) > 5:
        ad["scenes"] = scenes[:5]
    else:
        ad["scenes"] = scenes

    # Ensure required top-level keys exist
    ad.setdefault("headline", "New product, big upgrade")
    ad.setdefault("cta", "Order now")

    # Normalize scene fields
    for sc in ad["scenes"]:
        sc.setdefault("seconds", 4)
        sc.setdefault("caption", "Learn more")
        sc.setdefault("narration", "Discover what makes it great.")
        sc.setdefault("visual_prompt", "A clean product shot, modern lighting, premium look, vertical composition.")
        # Clamp seconds
        try:
            sc["seconds"] = int(sc["seconds"])
        except Exception:
            sc["seconds"] = 4
        sc["seconds"] = max(3, min(7, sc["seconds"]))

    return ad


def gen_image(prompt: str, out_path: Path):
    """
    Generate one PNG image for a scene (base64).
    DALL·E 3 supports response_format=b64_json.
    """
    img = client.images.generate(
        model=MODEL_IMAGE,
        prompt=prompt,
        size="1024x1024",
        response_format="b64_json",
    )
    b64 = img.data[0].b64_json
    out_path.write_bytes(base64.b64decode(b64))


def tts(narration: str, out_path: Path):
    """
    Generate voiceover audio (mp3).
    """
    audio = client.audio.speech.create(
        model=MODEL_TTS,
        voice=VOICE,
        input=narration
    )
    out_path.write_bytes(audio.read())


def mk_segment(img_path: Path, caption: str, seconds: int, out_path: Path):
    """
    Create a vertical video segment from an image:
    - scale to cover 1080x1920 then crop (prevents crop-too-big errors)
    - subtle zoom
    - caption overlay
    """
    caption = safe_drawtext(caption)

    font = "/System/Library/Fonts/Helvetica.ttc"
    if not Path(font).exists():
        font = ""

    wrapped = "\n".join(textwrap.wrap(caption, width=18))
    wrapped = safe_drawtext(wrapped)

    vf = (
        f"scale={OUT_W}:{OUT_H}:force_original_aspect_ratio=increase,"
        f"crop={OUT_W}:{OUT_H},"
        f"zoompan=z='min(1.12,1+0.0015*on)':d={seconds*FPS}:s={OUT_W}x{OUT_H},"
        f"drawbox=x=0:y={int(OUT_H*0.74)}:w={OUT_W}:h={int(OUT_H*0.26)}:color=black@0.35:t=fill,"
        f"drawtext=fontfile='{font}':text='{wrapped}':"
        f"x=(w-text_w)/2:y={int(OUT_H*0.80)}:"
        f"fontsize=54:fontcolor=white:line_spacing=12"
    )

    run([
        "ffmpeg", "-y",
        "-loop", "1",
        "-t", str(seconds),
        "-i", str(img_path),
        "-vf", vf,
        "-r", str(FPS),
        "-pix_fmt", "yuv420p",
        str(out_path)
    ])


def concat_with_audio(segments: list[Path], audio_path: Path, out_path: Path):
    """
    Concatenate segments reliably by writing only filenames into segments.txt
    and running ffmpeg from the workdir.
    """
    workdir = out_path.parent  # e.g. out/ad_xxxx
    list_file = workdir / "segments.txt"

    # Write only basenames so no path duplication occurs
    list_file.write_text("\n".join([f"file '{p.name}'" for p in segments]))

    # Concatenate segments into video_noaudio.mp4 (in workdir)
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "segments.txt", "-c", "copy", "video_noaudio.mp4"],
        check=True,
        cwd=str(workdir),
    )

    # Mux narration audio (also referenced by basename)
    subprocess.run(
        ["ffmpeg", "-y",
         "-i", "video_noaudio.mp4",
         "-i", audio_path.name,
         "-c:v", "copy",
         "-c:a", "aac",
         "-shortest",
         out_path.name],
        check=True,
        cwd=str(workdir),
    )


def main():
    product_desc = input("\nPaste product description:\n> ").strip()
    platform = input("Platform (TikTok/IG/YT) [TikTok]: ").strip() or "TikTok"
    tone = input("Tone (Bold/Clean/Fun) [Bold]: ").strip() or "Bold"

    workdir = Path("out") / f"ad_{uuid.uuid4().hex[:8]}"
    workdir.mkdir(parents=True, exist_ok=True)

    print("\n1) Generating ad plan (scenes)...")
    ad = make_scenes(product_desc, platform=platform, tone=tone)
    (workdir / "ad.json").write_text(json.dumps(ad, indent=2))

    print("2) Generating images...")
    img_paths: list[Path] = []
    for i, sc in enumerate(ad["scenes"], start=1):
        img_path = workdir / f"scene_{i}.png"
        prompt = (
            "Create a high-quality product ad visual. "
            f"{sc['visual_prompt']}. "
            "Vertical-friendly composition, modern lighting, premium look, no text, no logos."
        )
        gen_image(prompt, img_path)
        img_paths.append(img_path)
        print(f"   - scene {i} image ok")

    print("3) Generating voiceover...")
    narration = " ".join([sc["narration"] for sc in ad["scenes"]])
    audio_path = workdir / "voice.mp3"
    tts(narration, audio_path)

    print("4) Building video segments...")
    segments: list[Path] = []
    for i, sc in enumerate(ad["scenes"], start=1):
        seg_path = workdir / f"seg_{i}.mp4"
        mk_segment(img_paths[i - 1], sc["caption"], int(sc["seconds"]), seg_path)
        segments.append(seg_path)
        print(f"   - scene {i} segment ok")

    print("5) Concatenating + adding audio...")
    out_path = workdir / "final_ad.mp4"
    concat_with_audio(segments, audio_path, out_path)

    print(f"\n✅ Done: {out_path.as_posix()}")
    print(f"   Headline: {ad.get('headline', '')}")
    print(f"   CTA: {ad.get('cta', '')}")
    print(f"   Folder: {workdir.as_posix()}")


if __name__ == "__main__":
    main()
