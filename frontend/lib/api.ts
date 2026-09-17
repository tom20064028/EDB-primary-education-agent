import type {
  Change,
  ChatResponse,
  DemoMutation,
  Health,
  NotificationResult,
  RefreshResponse,
  Source,
} from "@/lib/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

type ApiValidationIssue = {
  msg?: unknown;
};

function readableApiDetail(body: unknown, fallback: string): string {
  if (!body || typeof body !== "object" || !("detail" in body)) return fallback;

  const detail = (body as { detail?: unknown }).detail;
  if (typeof detail === "string" && detail.trim()) return detail;

  if (Array.isArray(detail)) {
    const messages = detail
      .map((issue: ApiValidationIssue) => (typeof issue?.msg === "string" ? issue.msg : null))
      .filter((message): message is string => Boolean(message));
    if (messages.length) return messages.join(" ");
  }

  if (detail && typeof detail === "object" && "message" in detail) {
    const message = (detail as { message?: unknown }).message;
    if (typeof message === "string" && message.trim()) return message;
  }

  return fallback;
}

async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });

  if (!response.ok) {
    const fallback = `Request failed with HTTP ${response.status}`;
    let detail = fallback;
    try {
      detail = readableApiDetail(await response.json(), fallback);
    } catch {
      // Keep the safe status-based message when a proxy returns non-JSON content.
    }
    throw new Error(detail);
  }
  return (await response.json()) as T;
}

export const api = {
  health: () => apiRequest<Health>("/health"),
  sources: () => apiRequest<Source[]>("/api/sources"),
  changes: () => apiRequest<Change[]>("/api/changes"),
  bootstrap: () => apiRequest<RefreshResponse>("/api/sources/bootstrap", { method: "POST" }),
  refresh: (notify = true) =>
    apiRequest<RefreshResponse>("/api/sources/refresh", {
      method: "POST",
      body: JSON.stringify({ notify }),
    }),
  ask: (question: string) =>
    apiRequest<ChatResponse>("/api/chat", {
      method: "POST",
      body: JSON.stringify({ question }),
    }),
  mutateDemo: () =>
    apiRequest<DemoMutation>("/api/demo/mutate-snapshot", { method: "POST" }),
  testWebhook: () =>
    apiRequest<NotificationResult>("/api/notifications/test", {
      method: "POST",
      body: JSON.stringify({ message: "The EDB Agent webhook connection is working." }),
    }),
};
