from pathlib import Path
import subprocess
import sys


def generate_video(product_desc: str, platform: str, tone: str, repo_root: Path) -> Path:
    cmd = [
        sys.executable,
        str(repo_root / "generate_ad_video.py"),
        "--desc", product_desc,
        "--platform", platform,
        "--tone", tone,
    ]

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=str(repo_root),
        bufsize=1,
    )

    assert proc.stdout is not None
    for line in proc.stdout:
        print("[generate_ad_video]", line.rstrip())

    rc = proc.wait(timeout=900)  # 15 min
    if rc != 0:
        raise RuntimeError(f"Video generation failed with exit code {rc}")

    out_dir = repo_root / "out"
    candidates = sorted(out_dir.glob("ad_*"), key=lambda d: d.stat().st_mtime, reverse=True)
    for d in candidates:
        mp4 = d / "final_ad.mp4"
        if mp4.exists():
            return mp4

    raise RuntimeError("final_ad.mp4 not found after generation")