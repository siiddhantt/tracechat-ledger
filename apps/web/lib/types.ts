export type ConversationStatus = "active" | "cancelled";
export type MessageRole = "system" | "user" | "assistant";
export type ProviderName = "mock" | "openrouter" | "groq";

export type ChatMessage = {
  id: string;
  conversation_id: string;
  role: MessageRole;
  content: string;
  preview: string;
  created_at: string;
};

export type ConversationSummary = {
  id: string;
  title: string;
  status: ConversationStatus;
  created_at: string;
  updated_at: string;
  last_message_preview: string | null;
};

export type ConversationDetail = ConversationSummary & {
  messages: ChatMessage[];
};

export type ModelMetric = {
  provider: string;
  model: string;
  requests: number;
  errors: number;
  avg_latency_ms: number;
  total_tokens: number;
};

export type ThroughputPoint = {
  minute: string;
  requests: number;
  errors: number;
};

export type DashboardSummary = {
  total_requests: number;
  error_rate: number;
  avg_latency_ms: number;
  total_tokens: number;
  requests_per_minute: number;
  models: ModelMetric[];
  throughput: ThroughputPoint[];
  recent_errors: string[];
};
