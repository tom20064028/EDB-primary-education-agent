export type Health = {
  status: "ok";
  database_ready: boolean;
  llm_configured: boolean;
  webhook_configured: boolean;
};

export type Source = {
  url: string;
  title: string;
  content_hash: string | null;
  fetched_at: string | null;
  status: string;
  error: string | null;
  is_seed: boolean;
  chunk_count: number;
};

export type Citation = {
  title: string;
  section: string;
  url: string;
};

export type ToolTrace = {
  trace_id: string;
  tool_name: string;
  status: "success" | "error";
  duration_ms: number;
  result_count: number;
  safe_error_message: string | null;
};

export type ChatResponse = {
  answer: string;
  citations: Citation[];
  traces: ToolTrace[];
  mode: "llm-agent" | "retrieval-only";
  supported: boolean;
};

export type Change = {
  change_id: string;
  url: string;
  page_title: string;
  checked_at: string;
  old_hash: string;
  new_hash: string;
  added_text: string[];
  removed_text: string[];
  human_summary: string;
  notification_status: string;
  notification_error: string | null;
};

export type PageRefreshResult = {
  url: string;
  title: string;
  status: "unchanged" | "changed" | "new" | "failed";
  detail: string | null;
  change_id: string | null;
};

export type RefreshResponse = {
  checked_at: string;
  results: PageRefreshResult[];
  changes: Change[];
};

export type DemoMutation = {
  url: string;
  title: string;
  detail: string;
};

export type NotificationResult = {
  status: "sent" | "skipped" | "failed";
  detail: string;
};

