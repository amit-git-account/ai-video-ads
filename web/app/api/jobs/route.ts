import { NextResponse } from "next/server";
import { jobs } from "@/app/lib/jobs";

export async function POST() {
  const id = crypto.randomUUID();
  jobs.set(id, { createdAt: Date.now() });
  return NextResponse.json({ job_id: id });
}
