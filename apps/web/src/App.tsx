import {
  Activity,
  Ban,
  Bot,
  Gauge,
  ListRestart,
  MessageSquarePlus,
  PauseCircle,
  PlayCircle,
  RefreshCcw,
  Send,
  TriangleAlert,
} from "lucide-react";
import { FormEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  cancelConversation,
  getConversation,
  getDashboard,
  listConversations,
  resumeConversation,
  streamChat,
} from "@/lib/api";
import type {
  ChatMessage,
  ConversationSummary,
  DashboardSummary,
  ProviderName,
} from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

type DraftMessage = ChatMessage & { id: string };

const emptyDashboard: DashboardSummary = {
  total_requests: 0,
  error_rate: 0,
  avg_latency_ms: 0,
  total_tokens: 0,
  requests_per_minute: 0,
  models: [],
  throughput: [],
  recent_errors: [],
};

export default function Home() {
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [messages, setMessages] = useState<DraftMessage[]>([]);
  const [dashboard, setDashboard] = useState<DashboardSummary>(emptyDashboard);
  const [input, setInput] = useState("");
  const [provider, setProvider] = useState<ProviderName>("groq");
  const [model, setModel] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const selectedConversation = useMemo(
    () => conversations.find((conversation) => conversation.id === selectedId) ?? null,
    [conversations, selectedId],
  );

  const refresh = useCallback(async () => {
    const [conversationRows, dashboardSummary] = await Promise.all([
      listConversations(),
      getDashboard(),
    ]);
    setConversations(conversationRows);
    setDashboard(dashboardSummary);
    setSelectedId((current) => current ?? conversationRows[0]?.id ?? null);
  }, []);

  useEffect(() => {
    void refresh().catch((reason: unknown) => setError(messageFromError(reason)));
  }, [refresh]);

  useEffect(() => {
    if (isStreaming) {
      return;
    }
    if (!selectedId) {
      setMessages([]);
      return;
    }
    void getConversation(selectedId)
      .then((conversation) => setMessages(conversation.messages))
      .catch((reason: unknown) => setError(messageFromError(reason)));
  }, [isStreaming, selectedId]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const content = input.trim();
    if (!content || isStreaming) {
      return;
    }

    setError(null);
    setInput("");
    setIsStreaming(true);
    const controller = new AbortController();
    abortRef.current = controller;
    const assistantId = `assistant-${crypto.randomUUID()}`;
    const now = new Date().toISOString();

    setMessages((current) => [
      ...current,
      draftMessage("user", content, now),
      draftMessage("assistant", "", now, assistantId),
    ]);

    try {
      await streamChat(
        {
          conversation_id: selectedId ?? undefined,
          message: content,
          provider,
          model: model.trim() || undefined,
        },
        {
          onConversation: (conversationId) => setSelectedId(conversationId),
          onToken: (token) =>
            setMessages((current) =>
              current.some((message) => message.id === assistantId)
                ? current.map((message) =>
                    message.id === assistantId
                      ? { ...message, content: `${message.content}${token}` }
                      : message,
                  )
                : [...current, draftMessage("assistant", token, new Date().toISOString(), assistantId)],
            ),
          onDone: () => {
            setIsStreaming(false);
            void refresh();
          },
          onError: (message) => {
            setError(message);
            setIsStreaming(false);
            void refresh();
          },
        },
        controller.signal,
      );
    } catch (reason) {
      if (!(reason instanceof DOMException && reason.name === "AbortError")) {
        setError(messageFromError(reason));
      }
    } finally {
      abortRef.current = null;
      setIsStreaming(false);
    }
  }

  async function handleCancel() {
    if (selectedId) {
      await cancelConversation(selectedId).catch((reason: unknown) => setError(messageFromError(reason)));
    }
    abortRef.current?.abort();
    setIsStreaming(false);
    await refresh().catch((reason: unknown) => setError(messageFromError(reason)));
  }

  async function handleResume() {
    if (!selectedId) {
      return;
    }
    await resumeConversation(selectedId).catch((reason: unknown) => setError(messageFromError(reason)));
    await refresh().catch((reason: unknown) => setError(messageFromError(reason)));
  }

  function startNewConversation() {
    setSelectedId(null);
    setMessages([]);
    setError(null);
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-[1500px] flex-col gap-4 px-4 py-4 lg:px-6">
      <header className="flex flex-col gap-3 border-2 border-ink bg-paper p-4 shadow-sketch md:flex-row md:items-center md:justify-between">
        <div>
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center border-2 border-ink bg-marker shadow-sketchSoft">
              <Bot className="h-6 w-6" />
            </div>
            <div>
              <h1 className="font-display text-2xl font-black text-ink">TraceChat Ledger</h1>
              <p className="text-sm font-semibold text-neutral-700">
                Streaming chat, provider metadata, ingestion, and dashboards.
              </p>
            </div>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Select
            aria-label="Provider"
            className="w-40"
            value={provider}
            onChange={(event) => setProvider(event.target.value as ProviderName)}
          >
            <option value="mock">Mock</option>
            <option value="groq">Groq</option>
            <option value="openrouter">OpenRouter</option>
          </Select>
          <Input
            aria-label="Model"
            className="w-60"
            placeholder={
              provider === "groq"
                ? "openai/gpt-oss-120b"
                : provider === "openrouter"
                  ? "openai/gpt-4.1-mini"
                  : "mock/local-chat"
            }
            value={model}
            onChange={(event) => setModel(event.target.value)}
          />
          <Button title="Refresh data" variant="secondary" size="icon" onClick={() => void refresh()}>
            <RefreshCcw className="h-4 w-4" />
          </Button>
        </div>
      </header>

      <section className="grid flex-1 gap-4 lg:grid-cols-[300px_minmax(0,1fr)_330px]">
        <ConversationList
          conversations={conversations}
          selectedId={selectedId}
          onSelect={setSelectedId}
          onNew={startNewConversation}
        />

        <Card className="sketch-panel flex min-h-[620px] flex-col">
          <CardHeader className="flex flex-row items-center justify-between gap-3">
            <div>
              <CardTitle>{selectedConversation?.title ?? "New conversation"}</CardTitle>
              <div className="mt-2 flex items-center gap-2">
                <Badge tone={selectedConversation?.status === "cancelled" ? "red" : "green"}>
                  {selectedConversation?.status ?? "active"}
                </Badge>
                {isStreaming ? <Badge tone="blue">streaming</Badge> : null}
              </div>
            </div>
            <div className="flex items-center gap-2">
              {selectedConversation?.status === "cancelled" ? (
                <Button title="Resume conversation" size="icon" variant="secondary" onClick={handleResume}>
                  <PlayCircle className="h-4 w-4" />
                </Button>
              ) : (
                <Button
                  title="Cancel conversation"
                  size="icon"
                  variant="destructive"
                  onClick={handleCancel}
                  disabled={!selectedId && !isStreaming}
                >
                  <PauseCircle className="h-4 w-4" />
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent className="flex flex-1 flex-col gap-4">
            {error ? (
              <div className="flex items-start gap-2 border-2 border-ink bg-coral p-3 text-sm font-bold">
                <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0" />
                <span>{error}</span>
              </div>
            ) : null}

            <div className="flex-1 overflow-y-auto border-2 border-ink bg-white p-4">
              {messages.length ? (
                <div className="flex flex-col gap-3">
                  {messages.map((message) => (
                    <MessageBubble key={message.id} message={message} />
                  ))}
                </div>
              ) : (
                <div className="flex h-full min-h-[360px] items-center justify-center text-center">
                  <div className="border-2 border-dashed border-ink bg-marker px-5 py-4 font-black">
                    Start a logged chat
                  </div>
                </div>
              )}
            </div>

            <form className="flex flex-col gap-3" onSubmit={handleSubmit}>
              <Textarea
                aria-label="Message"
                placeholder="Ask about ingestion tradeoffs, scaling, or what this demo is tracking."
                value={input}
                onChange={(event) => setInput(event.target.value)}
                disabled={isStreaming || selectedConversation?.status === "cancelled"}
              />
              <div className="flex flex-wrap justify-between gap-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={handleCancel}
                  disabled={!isStreaming && !selectedId}
                >
                  <Ban className="h-4 w-4" />
                  Cancel
                </Button>
                <Button type="submit" disabled={isStreaming || selectedConversation?.status === "cancelled"}>
                  <Send className="h-4 w-4" />
                  Send
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        <DashboardPanel dashboard={dashboard} />
      </section>
    </main>
  );
}

function ConversationList({
  conversations,
  selectedId,
  onSelect,
  onNew,
}: {
  conversations: ConversationSummary[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
}) {
  return (
    <Card className="sketch-panel min-h-[620px]">
      <CardHeader className="flex flex-row items-center justify-between gap-2">
        <CardTitle>Conversations</CardTitle>
        <Button title="New conversation" size="icon" variant="secondary" onClick={onNew}>
          <MessageSquarePlus className="h-4 w-4" />
        </Button>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        {conversations.length ? (
          conversations.map((conversation) => (
            <button
              key={conversation.id}
              className={cn(
                "border-2 border-ink bg-white p-3 text-left shadow-sketchSoft transition hover:-translate-y-0.5 hover:bg-marker",
                selectedId === conversation.id && "bg-sky",
              )}
              onClick={() => onSelect(conversation.id)}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="line-clamp-1 text-sm font-black">{conversation.title}</span>
                <Badge tone={conversation.status === "cancelled" ? "red" : "green"}>
                  {conversation.status}
                </Badge>
              </div>
              <p className="mt-2 line-clamp-2 text-xs font-semibold text-neutral-700">
                {conversation.last_message_preview ?? "No messages yet"}
              </p>
            </button>
          ))
        ) : (
          <div className="border-2 border-dashed border-ink bg-white p-4 text-sm font-bold">
            No conversations yet
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function MessageBubble({ message }: { message: DraftMessage }) {
  const isUser = message.role === "user";
  return (
    <div className={cn("flex", isUser ? "justify-end" : "justify-start")}>
      <div
        className={cn(
          "max-w-[82%] whitespace-pre-wrap border-2 border-ink px-4 py-3 text-sm font-semibold shadow-sketchSoft",
          isUser ? "message-user" : "message-assistant",
        )}
      >
        {message.content || <span className="text-neutral-500">...</span>}
      </div>
    </div>
  );
}

function DashboardPanel({ dashboard }: { dashboard: DashboardSummary }) {
  return (
    <Card className="sketch-panel min-h-[620px]">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Dashboards</CardTitle>
          <Activity className="h-5 w-5" />
        </div>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <MetricGrid dashboard={dashboard} />

        <div className="border-2 border-ink bg-white p-3">
          <div className="mb-3 flex items-center gap-2 text-sm font-black">
            <Gauge className="h-4 w-4" />
            Model lanes
          </div>
          <div className="flex flex-col gap-2">
            {dashboard.models.length ? (
              dashboard.models.map((model) => (
                <div key={`${model.provider}-${model.model}`} className="border-2 border-ink bg-paper p-3">
                  <div className="flex items-center justify-between gap-2">
                    <span className="line-clamp-1 text-xs font-black">{model.model}</span>
                    <Badge tone={model.errors ? "red" : "green"}>{model.requests}</Badge>
                  </div>
                  <div className="mt-2 grid grid-cols-3 gap-2 text-xs font-bold text-neutral-700">
                    <span>{model.avg_latency_ms} ms</span>
                    <span>{model.errors} errors</span>
                    <span>{model.total_tokens} tokens</span>
                  </div>
                </div>
              ))
            ) : (
              <div className="border-2 border-dashed border-ink bg-paper p-3 text-sm font-bold">
                Waiting for logs
              </div>
            )}
          </div>
        </div>

        <div className="border-2 border-ink bg-white p-3">
          <div className="mb-3 flex items-center gap-2 text-sm font-black">
            <ListRestart className="h-4 w-4" />
            Throughput
          </div>
          <div className="flex h-28 items-end gap-1">
            {dashboard.throughput.length ? (
              dashboard.throughput.map((point) => (
                <div
                  key={point.minute}
                  title={`${point.requests} requests`}
                  className="min-h-2 flex-1 border-2 border-ink bg-sky"
                  style={{ height: `${Math.max(8, point.requests * 18)}px` }}
                />
              ))
            ) : (
              <div className="w-full border-2 border-dashed border-ink bg-paper p-3 text-sm font-bold">
                No traffic yet
              </div>
            )}
          </div>
        </div>

        {dashboard.recent_errors.length ? (
          <div className="border-2 border-ink bg-coral p-3">
            <div className="mb-2 text-sm font-black">Recent errors</div>
            <div className="flex flex-col gap-2">
              {dashboard.recent_errors.map((recentError) => (
                <p key={recentError} className="text-xs font-bold">
                  {recentError}
                </p>
              ))}
            </div>
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}

function MetricGrid({ dashboard }: { dashboard: DashboardSummary }) {
  const metrics = [
    ["Requests", dashboard.total_requests.toString(), "bg-marker"],
    ["Error rate", `${dashboard.error_rate}%`, "bg-coral"],
    ["Latency", `${dashboard.avg_latency_ms} ms`, "bg-mint"],
    ["Tokens", dashboard.total_tokens.toString(), "bg-sky"],
  ];
  return (
    <div className="grid grid-cols-2 gap-3">
      {metrics.map(([label, value, color]) => (
        <div key={label} className={cn("border-2 border-ink p-3 shadow-sketchSoft", color)}>
          <div className="text-xs font-black uppercase tracking-normal">{label}</div>
          <div className="mt-1 text-xl font-black">{value}</div>
        </div>
      ))}
    </div>
  );
}

function draftMessage(
  role: "user" | "assistant",
  content: string,
  createdAt: string,
  id = `${role}-${crypto.randomUUID()}`,
): DraftMessage {
  return {
    id,
    conversation_id: "draft",
    role,
    content,
    preview: content.slice(0, 280),
    created_at: createdAt,
  };
}

function messageFromError(reason: unknown) {
  return reason instanceof Error ? reason.message : "Request failed";
}
