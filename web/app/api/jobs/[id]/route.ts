import { NextResponse } from "next/server";
import { jobs } from "@/app/lib/jobs";

export async function GET(
  _req: Request,
  ctx: { params: Promise<{ id: string }> }
) {
  const { id } = await ctx.params;

  const job = jobs.get(id);
  if (!job) return NextResponse.json({ error: "not_found" }, { status: 404 });

  const elapsed = Date.now() - job.createdAt;
  const status = elapsed >= 5000 ? "done" : "queued";

  return NextResponse.json({ job_id: id, status });
}
