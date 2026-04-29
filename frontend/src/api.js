const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function request(path, init) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init.headers ?? {}),
    },
    ...init,
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed: ${response.status}`);
  }
  return response.json();
}

export function analyzeTriage(message) {
  return request("/api/triage/analyze", {
    method: "POST",
    body: JSON.stringify({ message, channel: "email" }),
  });
}

export function ingestListing(documentId, text) {
  return request("/api/quiz/ingest", {
    method: "POST",
    body: JSON.stringify({ document_id: documentId, text, metadata: { source: "ui" } }),
  });
}

export function generateQuiz(documentId, numQuestions) {
  return request("/api/quiz/generate", {
    method: "POST",
    body: JSON.stringify({ document_id: documentId, num_questions: numQuestions }),
  });
}

export function evaluateAnswer(payload) {
  return request("/api/quiz/evaluate", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

