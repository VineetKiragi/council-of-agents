const API_BASE = "http://localhost:8000/api";

async function handleResponse(response, context) {
  if (!response.ok) {
    let detail;
    try {
      const body = await response.json();
      detail = body.detail || JSON.stringify(body);
    } catch {
      detail = response.statusText;
    }
    throw new Error(`${context} failed (${response.status}): ${detail}`);
  }
  return response.json();
}

export async function createSession(prompt) {
  const response = await fetch(`${API_BASE}/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt }),
  });
  return handleResponse(response, "Create session");
}

export async function getSessions() {
  const response = await fetch(`${API_BASE}/sessions`);
  return handleResponse(response, "Get sessions");
}

export async function getSession(sessionId) {
  const response = await fetch(`${API_BASE}/sessions/${sessionId}`);
  return handleResponse(response, "Get session");
}
