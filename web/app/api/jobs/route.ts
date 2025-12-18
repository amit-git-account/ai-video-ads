import { NextResponse } from "next/server";
import { supabaseServer } from "../../lib/supabase-server";


export async function POST(req: Request) {
  console.log("POST /api/jobs hit");
  console.log("SUPABASE_URL:", process.env.NEXT_PUBLIC_SUPABASE_URL);
  console.log("HAS_SERVICE_KEY:", !!process.env.SUPABASE_SERVICE_ROLE_KEY);

  const body = await req.json().catch(() => ({}));
  const prompt = String(body.product_description ?? "").trim();
  const platform = String(body.platform ?? "TikTok");
  const tone = String(body.tone ?? "Bold");

  if (!prompt) {
    return NextResponse.json({ error: "missing_product_description" }, { status: 400 });
  }

  const supabase = supabaseServer();

  const { data, error } = await supabase
    .from("jobs")
    .insert([{ prompt, platform, tone, status: "queued" }])
    .select("id")
    .single();

  if (error || !data?.id) {
    console.error("Supabase insert error:", error);
    return NextResponse.json({ error: error?.message ?? "insert_failed" }, { status: 500 });
  }

  return NextResponse.json({
    job_id: data.id,
    supabase_url: process.env.NEXT_PUBLIC_SUPABASE_URL,
  });
}
