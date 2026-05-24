import type {
  ConversationDetail,
  ConversationSummary,
  DashboardSummary,
  ProviderName,
} from "@/lib/types";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

type StreamHandlers = {
  onConversation: (conversationId: string) => void;
  onToken: (content: string) => void;
  onDone: () => void;
  onError: (message: string) => void;
};

type ChatStreamRequest = {
  conversation_id?: string;
  message: string;
  provider: ProviderName;
  model?: string;
};

export async function listConversations() {
  return request<ConversationSummary[]>("/v1/conversations");
}

export async function getConversation(id: string) {
  return request<ConversationDetail>(`/v1/conversations/${id}`);
}

export async function cancelConversation(id: string) {
  return request<ConversationSummary>(`/v1/conversations/${id}/cancel`, { method: "PATCH" });
}

export async function resumeConversation(id: string) {
  return request<ConversationSummary>(`/v1/conversations/${id}/resume`, { method: "PATCH" });
}

export async function getDashboard() {
  return request<DashboardSummary>("/v1/dashboard/summary");
}

export async function streamChat(
  payload: ChatStreamRequest,
  handlers: StreamHandlers,
  signal: AbortSignal,
) {
  const response = await fetch(`${API_URL}/v1/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal,
  });

  if (!response.ok || !response.body) {
    throw new Error(await readError(response));
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  let isReading = true;
  while (isReading) {
    const { value, done } = await reader.read();
    isReading = !done;
    buffer += decoder.decode(value, { stream: !done });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";
    for (const part of parts) {
      handleSse(part, handlers);
    }
    if (done) {
      if (buffer.trim()) {
        handleSse(buffer, handlers);
      }
      break;
    }
  }
}

async function request<T>(path: string, init?: RequestInit) {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  return (await response.json()) as T;
}

function handleSse(raw: string, handlers: StreamHandlers) {
  const event = raw
    .split("\n")
    .find((line) => line.startsWith("event:"))
    ?.replace("event:", "")
    .trim();
  const dataLine = raw
    .split("\n")
    .find((line) => line.startsWith("data:"))
    ?.replace("data:", "")
    .trim();
  if (!event || !dataLine) {
    return;
  }
  const data = JSON.parse(dataLine) as Record<string, string>;
  if (event === "conversation" && data.conversation_id) {
    handlers.onConversation(data.conversation_id);
  }
  if (event === "token" && data.content) {
    handlers.onToken(data.content);
  }
  if (event === "done") {
    handlers.onDone();
  }
  if (event === "error") {
    handlers.onError(data.message ?? "Request failed");
  }
}

async function readError(response: Response) {
  try {
    const body = (await response.json()) as { error?: { message?: string } };
    return body.error?.message ?? response.statusText;
  } catch {
    return response.statusText || "Request failed";
  }
}
