import { NextResponse } from "next/server";
import { supabaseServer } from "../../../lib/supabase-server";

export async function GET(
  _req: Request,
  ctx: { params: Promise<{ id: string }> }
) {
  const { id } = await ctx.params;

  const supabase = supabaseServer();
  const { data, error } = await supabase
    .from("jobs")
    .select("id,status,result_url")
    .eq("id", id)
    .single();

  if (error || !data?.id) {
    return NextResponse.json({ error: "not_found" }, { status: 404 });
  }

  return NextResponse.json({
    job_id: data.id,
    status: data.status,
    result_url: data.result_url ?? null,
  });
}
