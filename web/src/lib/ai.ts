/** Server-side client for the FastAPI service. Never import this from a client component. */

export type Source = {
  id: number;
  course_code: string | null;
  title: string | null;
  doc_type: string | null;
  heading: string | null;
  source: string | null;
  url: string | null;
  score: number;
  snippet: string;
};

export type AskResponse = {
  answer: string;
  route: string;
  sources: Source[];
  latency_ms: number;
};

const AI_SERVICE_URL = process.env.AI_SERVICE_URL ?? "http://localhost:8000";

export async function ask(question: string): Promise<AskResponse> {
  const res = await fetch(`${AI_SERVICE_URL}/ask`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ question }),
    cache: "no-store",
    signal: AbortSignal.timeout(90_000),
  });
  if (!res.ok) {
    const detail = await res.text().catch(() => "");
    throw new Error(`AI service returned ${res.status}${detail ? `: ${detail}` : ""}`);
  }
  return res.json();
}
