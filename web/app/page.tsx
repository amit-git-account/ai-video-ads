"use client";

import { useEffect, useMemo, useState } from "react";

export default function Home() {
  const [desc, setDesc] = useState("");
  const [jobId, setJobId] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [resultUrl, setResultUrl] = useState<string | null>(null);

  const statusLabel = useMemo(() => {
    if (!status) return "Idle";
    if (status === "queued") return "Queued";
    if (status === "processing") return "Generating…";
    if (status === "done") return "Done";
    if (status === "failed") return "Failed";
    return status;
  }, [status]);

  useEffect(() => {
    if (!jobId) return;
    let t: any;

    const poll = async () => {
      const res = await fetch(`/api/jobs/${jobId}`, { cache: "no-store" });
      if (!res.ok) return;
      const data = await res.json();

      setStatus(data.status);
      setResultUrl(data.result_url ?? null);

      if (data.status !== "done" && data.status !== "failed") {
        t = setTimeout(poll, 1200);
      }
    };

    poll();
    return () => t && clearTimeout(t);
  }, [jobId]);

  const createJob = async () => {
    setStatus("queued");
    setResultUrl(null);

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
  };

  const disabled = !desc.trim() || status === "queued" || status === "processing";

  return (
    <main
      style={{
        minHeight: "100vh",
        padding: "48px 18px",
        background:
          "radial-gradient(1200px 600px at 20% 0%, rgba(99,102,241,0.25), transparent), radial-gradient(1000px 600px at 80% 10%, rgba(236,72,153,0.18), transparent), #0b0f19",
        color: "white",
        fontFamily: "system-ui, -apple-system, Segoe UI, Roboto, Arial",
      }}
    >
      <div style={{ maxWidth: 980, margin: "0 auto" }}>
        {/* Header */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            gap: 16,
            marginBottom: 28,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div
              style={{
                width: 38,
                height: 38,
                borderRadius: 12,
                background: "linear-gradient(135deg, rgba(99,102,241,1), rgba(236,72,153,1))",
                boxShadow: "0 10px 30px rgba(0,0,0,0.35)",
              }}
            />
            <div style={{ fontWeight: 800, letterSpacing: 0.1,fontSize: 64, lineHeight: 1 }}>AI Video Ads</div>
          </div>

          <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
            <span
              style={{
                padding: "8px 12px",
                borderRadius: 999,
                background: "rgba(255,255,255,0.08)",
                border: "1px solid rgba(255,255,255,0.12)",
                fontSize: 13,
              }}
            >
              Status: <b>{statusLabel}</b>
            </span>
          </div>
        </div>

        {/* Hero */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1.15fr 0.85fr",
            gap: 22,
            alignItems: "stretch",
          }}
        >
          <div
            style={{
              padding: 22,
              borderRadius: 18,
              background: "rgba(255,255,255,0.06)",
              border: "1px solid rgba(255,255,255,0.12)",
              boxShadow: "0 18px 50px rgba(0,0,0,0.35)",
            }}
          >
            <h1 style={{ fontSize: 44, lineHeight: 1.05, margin: 0 }}>
              Turn a product description into a <span style={{ color: "#a5b4fc" }}>TikTok-style video ad</span>
            </h1>
            <p style={{ marginTop: 12, marginBottom: 18, color: "rgba(255,255,255,0.78)", fontSize: 16 }}>
              Paste a description → we generate scenes, images, audio, and stitch a short ad video. Async job + download link.
            </p>

            <div
              style={{
                display: "grid",
                gridTemplateColumns: "1fr",
                gap: 10,
                marginTop: 12,
              }}
            >
              <textarea
                value={desc}
                onChange={(e) => setDesc(e.target.value)}
                placeholder="Example: Noise-canceling wireless earbuds for runners. Sweatproof, 10-hour battery, punchy bass."
                rows={7}
                style={{
                  width: "100%",
                  padding: 14,
                  borderRadius: 14,
                  background: "rgba(10,14,26,0.7)",
                  color: "white",
                  border: "1px solid rgba(255,255,255,0.12)",
                  outline: "none",
                  resize: "vertical",
                }}
              />

              <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
                <button
                  onClick={createJob}
                  disabled={disabled}
                  style={{
                    padding: "12px 16px",
                    borderRadius: 14,
                    border: "1px solid rgba(255,255,255,0.16)",
                    background: disabled
                      ? "rgba(255,255,255,0.08)"
                      : "linear-gradient(135deg, rgba(99,102,241,1), rgba(236,72,153,1))",
                    color: "white",
                    fontWeight: 700,
                    cursor: disabled ? "not-allowed" : "pointer",
                    boxShadow: disabled ? "none" : "0 16px 40px rgba(0,0,0,0.35)",
                  }}
                >
                  {status === "processing" ? "Generating…" : "Generate video"}
                </button>

                {jobId && (
                  <span style={{ color: "rgba(255,255,255,0.7)", fontSize: 13 }}>
                    Job: <code style={{ color: "rgba(255,255,255,0.9)" }}>{jobId}</code>
                  </span>
                )}

                {status === "done" && resultUrl && (
                  <a
                    href={resultUrl}
                    target="_blank"
                    rel="noreferrer"
                    style={{
                      marginLeft: "auto",
                      padding: "12px 16px",
                      borderRadius: 14,
                      background: "rgba(255,255,255,0.10)",
                      border: "1px solid rgba(255,255,255,0.16)",
                      color: "white",
                      textDecoration: "none",
                      fontWeight: 700,
                    }}
                  >
                    Download video →
                  </a>
                )}
              </div>

              {status === "failed" && (
                <div
                  style={{
                    marginTop: 8,
                    padding: 12,
                    borderRadius: 14,
                    background: "rgba(239,68,68,0.12)",
                    border: "1px solid rgba(239,68,68,0.25)",
                    color: "rgba(255,255,255,0.9)",
                  }}
                >
                  Generation failed. Try a shorter prompt, or retry in a minute.
                </div>
              )}
            </div>
          </div>

          {/* Right card */}
          <div
            style={{
              padding: 22,
              borderRadius: 18,
              background: "rgba(255,255,255,0.04)",
              border: "1px solid rgba(255,255,255,0.10)",
            }}
          >
            <div style={{ fontSize: 14, color: "rgba(255,255,255,0.75)", marginBottom: 10 }}>
              What you get
            </div>

            <ul style={{ margin: 0, paddingLeft: 18, color: "rgba(255,255,255,0.85)", lineHeight: 1.7 }}>
              <li>Short multi-scene ad video (MP4)</li>
              <li>Voiceover + background music</li>
              <li>R2 download link when done</li>
            </ul>

            <div style={{ height: 14 }} />

            <div
              style={{
                borderRadius: 16,
                overflow: "hidden",
                border: "1px solid rgba(255,255,255,0.10)",
                background: "rgba(0,0,0,0.25)",
              }}
            >
              <div style={{ padding: 14, fontSize: 13, color: "rgba(255,255,255,0.78)" }}>
                Tip: keep descriptions <b>1–2 sentences</b> for faster renders.
              </div>
              <div style={{ padding: 14, borderTop: "1px solid rgba(255,255,255,0.08)" }}>
                <div style={{ fontSize: 13, color: "rgba(255,255,255,0.72)" }}>Example prompts</div>
                <div style={{ marginTop: 10, display: "grid", gap: 8 }}>
                  {[
                    "Protein bar for busy professionals — 20g protein, no sugar crash.",
                    "AI resume checker for developers — fixes bullets + ATS keywords.",
                    "Yoga mat that doesn’t slip — extra grip, easy carry strap.",
                  ].map((p) => (
                    <button
                      key={p}
                      onClick={() => setDesc(p)}
                      style={{
                        textAlign: "left",
                        padding: "10px 12px",
                        borderRadius: 14,
                        background: "rgba(255,255,255,0.06)",
                        border: "1px solid rgba(255,255,255,0.10)",
                        color: "rgba(255,255,255,0.9)",
                        cursor: "pointer",
                      }}
                    >
                      {p}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div style={{ marginTop: 14, fontSize: 12, color: "rgba(255,255,255,0.55)" }}>
              MVP note: results are generated asynchronously (polling).
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}