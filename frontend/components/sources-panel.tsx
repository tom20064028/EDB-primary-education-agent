"use client";

import { DatabaseIcon, ExternalIcon } from "@/components/icons";
import { StatusPill } from "@/components/status-pill";
import type { Health, Source } from "@/lib/types";

type SourcesPanelProps = {
  health: Health | null;
  sources: Source[];
  busy: boolean;
  onBootstrap: () => Promise<void>;
};

function sourceTone(status: string): "good" | "warning" | "neutral" | "error" {
  if (status === "ready") return "good";
  if (status === "stale") return "warning";
  if (status === "failed") return "error";
  return "neutral";
}

export function SourcesPanel({ health, sources, busy, onBootstrap }: SourcesPanelProps) {
  const readyCount = sources.filter((source) => source.status === "ready").length;
  const totalChunks = sources.reduce((total, source) => total + source.chunk_count, 0);

  return (
    <section aria-labelledby="sources-title" className="panel sources-panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Controlled knowledge base</p>
          <h2 id="sources-title">Source status</h2>
        </div>
        <DatabaseIcon size={23} />
      </div>

      <div className="metric-grid">
        <div><strong>{readyCount}/{sources.length || 0}</strong><span>pages ready</span></div>
        <div><strong>{totalChunks}</strong><span>search chunks</span></div>
        <div><strong>{health?.llm_configured ? "On" : "Off"}</strong><span>LLM agent</span></div>
      </div>

      {!sources.length ? (
        <div className="setup-card">
          <p>No source baseline exists yet. Initialization discovers the seed page&apos;s direct content links and caches each approved page.</p>
          <button className="button button-primary" disabled={busy} onClick={onBootstrap} type="button">
            {busy ? "Initializing…" : "Initialize sources"}
          </button>
        </div>
      ) : (
        <div className="source-list">
          {sources.map((source) => (
            <a href={source.url} key={source.url} rel="noreferrer" target="_blank">
              <span className="source-index">{source.is_seed ? "00" : String(sources.indexOf(source)).padStart(2, "0")}</span>
              <span className="source-name">
                <strong>{source.title}</strong>
                <small>{source.chunk_count} chunks{source.error ? ` · ${source.error}` : ""}</small>
              </span>
              <StatusPill tone={sourceTone(source.status)}>{source.status}</StatusPill>
              <ExternalIcon />
            </a>
          ))}
        </div>
      )}
    </section>
  );
}

