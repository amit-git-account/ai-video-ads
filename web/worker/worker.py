import os
import time
from pathlib import Path

from dotenv import load_dotenv

# ✅ Load env FIRST, before other imports
load_dotenv(dotenv_path=Path(__file__).with_name(".env"))

# Now it’s safe to import modules that read env vars
from supabase import create_client
from video_pipeline import generate_video
from r2_upload import upload_mp4, signed_download_url


# 👇 LOAD .env EXPLICITLY
load_dotenv(dotenv_path=Path(__file__).with_name(".env"))


def find_repo_root(start: Path) -> Path:
    p = start.resolve()
    for _ in range(10):  # walk up a few levels
        if (p / "generate_ad_video.py").exists():
            return p
        p = p.parent
    raise RuntimeError("Could not find repo root (generate_ad_video.py not found in parents).")



def sb():
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])


def claim_one_job():
    client = sb()
    res = (
        client.table("jobs")
        .select("id,prompt,platform,tone,status")
        .eq("status", "queued")
        .order("created_at", desc=False)
        .limit(1)
        .execute()
    )
    rows = res.data or []
    if not rows:
        return None

    job = rows[0]
    upd = (
        client.table("jobs")
        .update({"status": "planning"})
        .eq("id", job["id"])
        .eq("status", "queued")
        .execute()
    )
    if not upd.data:
        return None
    return job


def set_status(job_id: str, status: str, result_url: str | None = None):
    payload = {"status": status}
    if result_url is not None:
        payload["result_url"] = result_url
    sb().table("jobs").update(payload).eq("id", job_id).execute()


def main():
    load_dotenv()
    repo_root = find_repo_root(Path(__file__))
    print("Repo root:", repo_root)
    print("Exists generate_ad_video.py:", (repo_root / "generate_ad_video.py").exists())



    print("Worker started. Polling for jobs...")

    while True:
        job = claim_one_job()
        if not job:
            time.sleep(2)
            continue

        job_id = job["id"]
        prompt = job["prompt"]
        platform = job.get("platform") or "TikTok"
        tone = job.get("tone") or "Bold"

        print(f"Processing job {job_id}...")

        try:
            print("HAS OPENAI KEY:", bool(os.environ.get("OPENAI_API_KEY")))
            print("Starting generate_video() now...")
            set_status(job_id, "generating")

            mp4_path = generate_video(prompt, platform, tone, repo_root)
            set_status(job_id, "uploading")

            key = f"jobs/{job_id}/final_ad.mp4"

            upload_mp4(mp4_path, key)
            url = signed_download_url(key, expires_seconds=3600)

            set_status(job_id, "done", result_url=url)
            print(f"✅ Done {job_id}")

        except Exception as e:
            print(f"❌ Failed {job_id}: {e}")
            set_status(job_id, "failed", result_url=None)


if __name__ == "__main__":
    main()
