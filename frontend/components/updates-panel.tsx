"use client";

import { PulseIcon } from "@/components/icons";
import { StatusPill } from "@/components/status-pill";
import type { Change, PageRefreshResult } from "@/lib/types";

type UpdatesPanelProps = {
  changes: Change[];
  latestResults: PageRefreshResult[];
  sourcesReady: boolean;
  webhookConfigured: boolean;
  busy: string | null;
  notice: string | null;
  onRefresh: () => Promise<void>;
  onMutate: () => Promise<void>;
  onTestWebhook: () => Promise<void>;
};

function formatDate(value: string) {
  return new Intl.DateTimeFormat("zh-HK", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

export function UpdatesPanel({
  changes,
  latestResults,
  sourcesReady,
  webhookConfigured,
  busy,
  notice,
  onRefresh,
  onMutate,
  onTestWebhook,
}: UpdatesPanelProps) {
  const changed = latestResults.filter((result) => result.status === "changed").length;
  const failed = latestResults.filter((result) => result.status === "failed").length;

  return (
    <section aria-labelledby="updates-title" className="panel updates-panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Snapshot monitor</p>
          <h2 id="updates-title">Updates</h2>
        </div>
        <PulseIcon size={24} />
      </div>

      <div className="action-grid">
        <button className="button button-primary" disabled={!sourcesReady || Boolean(busy)} onClick={onRefresh} type="button">
          {busy === "refresh" ? "Checking pages…" : "Check for updates"}
        </button>
        <button className="button button-secondary" disabled={!sourcesReady || Boolean(busy)} onClick={onMutate} type="button">
          {busy === "mutate" ? "Applying…" : "Inject demo change"}
        </button>
        <button className="button button-quiet" disabled={!webhookConfigured || Boolean(busy)} onClick={onTestWebhook} type="button">
          {busy === "webhook" ? "Sending…" : "Test webhook"}
        </button>
      </div>

      {notice ? <p className="operation-notice" role="status">{notice}</p> : null}

      {latestResults.length ? (
        <div className="run-summary">
          <span>Latest check</span>
          <strong>{changed} changed · {failed} failed · {latestResults.length - changed - failed} unchanged/new</strong>
        </div>
      ) : null}

      <div className="change-list">
        {changes.length ? changes.map((change) => (
          <article className="change-card" key={change.change_id}>
            <div className="change-card-heading">
              <div>
                <strong>{change.page_title}</strong>
                <small>{formatDate(change.checked_at)}</small>
              </div>
              <StatusPill tone={change.notification_status === "sent" ? "good" : "neutral"}>
                notify: {change.notification_status}
              </StatusPill>
            </div>
            <p>{change.human_summary}</p>
            <details>
              <summary>Inspect text diff</summary>
              {change.added_text.map((line) => <p className="diff-added" key={`add-${line}`}>+ {line}</p>)}
              {change.removed_text.map((line) => <p className="diff-removed" key={`remove-${line}`}>− {line}</p>)}
            </details>
          </article>
        )) : (
          <div className="empty-updates">
            <p>No meaningful content changes have been recorded.</p>
            <small>Use the clearly labelled demo action, then run a live refresh to exercise the full diff path.</small>
          </div>
        )}
      </div>
    </section>
  );
}

