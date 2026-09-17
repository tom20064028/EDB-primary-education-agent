"use client";

import { FormEvent, useState } from "react";

import { ExternalIcon, SearchIcon } from "@/components/icons";
import { StatusPill } from "@/components/status-pill";
import type { ChatResponse } from "@/lib/types";

type AskPanelProps = {
  onAsk: (question: string) => Promise<ChatResponse>;
  sourcesReady: boolean;
};

const EXAMPLE_QUESTIONS = ["甚麼是「一條龍」辦學模式？", "小學全日制有甚麼背景？", "教育局有沒有提供校服折扣？"];

export function AskPanel({ onAsk, sourcesReady }: AskPanelProps) {
  const [question, setQuestion] = useState("");
  const [response, setResponse] = useState<ChatResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const value = question.trim();
    if (!value || loading) return;
    setResponse(null);
    if (value.length < 2) {
      setError("請輸入至少 2 個字元嘅問題。");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      setResponse(await onAsk(value));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "The question could not be processed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section aria-labelledby="ask-title" className="panel ask-panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Grounded Q&amp;A</p>
          <h2 id="ask-title">Ask the EDB sources</h2>
        </div>
        <StatusPill tone={sourcesReady ? "good" : "warning"}>{sourcesReady ? "Sources ready" : "Setup required"}</StatusPill>
      </div>

      <form className="question-form" onSubmit={submit}>
        <label htmlFor="question">Question</label>
        <div className="question-input-row">
          <textarea
            disabled={!sourcesReady || loading}
            id="question"
            maxLength={1000}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="例如：甚麼是小班教學？"
            rows={3}
            value={question}
          />
          <button className="send-button" disabled={!sourcesReady || !question.trim() || loading} type="submit">
            <SearchIcon size={19} />
            <span>{loading ? "Searching…" : "Ask"}</span>
          </button>
        </div>
      </form>

      <div aria-label="Example questions" className="question-chips">
        {EXAMPLE_QUESTIONS.map((example) => (
          <button disabled={!sourcesReady || loading} key={example} onClick={() => setQuestion(example)} type="button">
            {example}
          </button>
        ))}
      </div>

      {error ? <p className="inline-error" role="alert">{error}</p> : null}

      {response ? (
        <article className={`answer-card ${response.supported ? "" : "answer-unsupported"}`}>
          <div className="answer-meta">
            <StatusPill tone={response.supported ? "good" : "warning"}>
              {response.supported ? "Source evidence found" : "Insufficient evidence"}
            </StatusPill>
            <span>{response.mode === "llm-agent" ? "LLM agent" : "Retrieval-only mode"}</span>
          </div>
          <p className="answer-text">{response.answer}</p>
          {response.citations.length ? (
            <div className="citations">
              <h3>Sources</h3>
              {response.citations.map((citation) => (
                <a href={citation.url} key={`${citation.url}-${citation.section}`} rel="noreferrer" target="_blank">
                  <span>
                    <strong>{citation.title}</strong>
                    <small>{citation.section}</small>
                  </span>
                  <ExternalIcon />
                </a>
              ))}
            </div>
          ) : null}
          <details className="trace-details">
            <summary>Agent tool trace</summary>
            {response.traces.map((trace) => (
              <div className="trace-row" key={trace.trace_id}>
                <code>{trace.tool_name}</code>
                <span>{trace.status}</span>
                <span>{trace.result_count} results</span>
                <span>{trace.duration_ms} ms</span>
              </div>
            ))}
          </details>
        </article>
      ) : (
        <div className="empty-answer">
          <SearchIcon size={24} />
          <p>Answers are limited to cached, allowlisted EDB pages and include source links.</p>
        </div>
      )}
    </section>
  );
}
