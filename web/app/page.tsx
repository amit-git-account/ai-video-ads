"use client";

import { useEffect, useState } from "react";

export default function Home() {
  const [desc, setDesc] = useState("");
  const [jobId, setJobId] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [resultUrl, setResultUrl] = useState<string | null>(null);

  useEffect(() => {
    if (!jobId) return;
    let t: any;

    const poll = async () => {
      const res = await fetch(`/api/jobs/${jobId}`);
      if (!res.ok) return;
      const data = await res.json();
      setStatus(data.status);
      setResultUrl(data.result_url ?? null);
      if (data.status !== "done") {
        t = setTimeout(poll, 1000);
      }
    };

    poll();
    return () => t && clearTimeout(t);
  }, [jobId]);

  const createJob = async () => {
    setStatus(null);
    const res = await fetch("/api/jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        product_description: desc,
        platform: "TikTok",
        tone: "Bold",
      }),
    });
    const data = await res.json();
    setJobId(data.job_id);
    setStatus("queued");
  };

  return (
    <main style={{ maxWidth: 720, margin: "40px auto", fontFamily: "system-ui" }}>
      <h1>AI Video Ads MVP</h1>
      <p>Paste a product description → generate a short video ad.</p>

      <textarea
        value={desc}
        onChange={(e) => setDesc(e.target.value)}
        placeholder="e.g. Wireless earbuds with noise canceling..."
        rows={6}
        style={{ width: "100%", padding: 12 }}
      />

      <div style={{ marginTop: 12 }}>
        <button onClick={createJob} disabled={!desc.trim()}>
          Generate
        </button>
      </div>

      {jobId && (
        <div style={{ marginTop: 20 }}>
          <div><b>Job ID:</b> {jobId}</div>
          <div><b>Status:</b> {status}</div>
          {status === "done" && resultUrl && (
        <div style={{ marginTop: 12 }}>
        <a href={resultUrl} target="_blank" rel="noreferrer">
        Download video
      </a>
    </div>
)}
        </div>
      )}
    </main>
  );
}
