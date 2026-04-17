/**
 * Tiny typed client for the cv-engine FastAPI backend.
 *
 * Base URL comes from VITE_API_URL (injected by vite.config.ts). Defaults to
 * the Render deployment so local dev can render the live feed without config.
 */

const API_URL = import.meta.env.VITE_API_URL as string;

export type LocationBand = "PASS" | "REVIEW" | "FAIL" | "NO_DATA";
export type RunStatus = "queued" | "processing" | "succeeded" | "failed" | "flagged_for_review";

export interface TopCategory {
  label: string;
  score: number;
  max: number;
}

export interface RunSummary {
  run_id: number;
  cv_id: string;
  candidate_name: string | null;
  status: RunStatus;
  started_at: string;
  completed_at: string | null;
  score_total: number | null;
  location_band: LocationBand | null;
  is_reapplication: boolean;
  top_categories: TopCategory[];
}

export interface RunResult {
  run_id: number;
  cv_id: string;
  status: "succeeded" | "failed" | "flagged_for_review";
  location_band: LocationBand;
  score_total: number | null;
  scores: Record<string, number> | null;
  justifications: Record<string, string> | null;
  flags: string[];
  last_error: string | null;
}

export async function listRuns(limit = 50): Promise<RunSummary[]> {
  const res = await fetch(`${API_URL}/runs?limit=${limit}`);
  if (!res.ok) throw new Error(`GET /runs failed: ${res.status}`);
  const body = await res.json();
  return body.runs as RunSummary[];
}

export async function processCV(file: File, emailBody?: string): Promise<RunResult> {
  const form = new FormData();
  form.append("cv", file);
  if (emailBody) form.append("email_body", emailBody);
  form.append("source", "direct");

  const res = await fetch(`${API_URL}/process`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`POST /process failed (${res.status}): ${text}`);
  }
  return (await res.json()) as RunResult;
}

export { API_URL };
