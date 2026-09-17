"use client";

import { useCallback, useEffect, useState } from "react";

import { ArrowIcon } from "@/components/icons";
import { AskPanel } from "@/components/ask-panel";
import { SourcesPanel } from "@/components/sources-panel";
import { StatusPill } from "@/components/status-pill";
import { UpdatesPanel } from "@/components/updates-panel";
import { api } from "@/lib/api";
import type { Change, Health, PageRefreshResult, Source } from "@/lib/types";

export function Dashboard() {
  const [health, setHealth] = useState<Health | null>(null);
  const [sources, setSources] = useState<Source[]>([]);
  const [changes, setChanges] = useState<Change[]>([]);
  const [latestResults, setLatestResults] = useState<PageRefreshResult[]>([]);
  const [busy, setBusy] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [connectionError, setConnectionError] = useState<string | null>(null);

  const loadDashboard = useCallback(async () => {
    try {
      const [nextHealth, nextSources, nextChanges] = await Promise.all([
        api.health(),
        api.sources(),
        api.changes(),
      ]);
      setHealth(nextHealth);
      setSources(nextSources);
      setChanges(nextChanges);
      setConnectionError(null);
    } catch (caught) {
      setConnectionError(caught instanceof Error ? caught.message : "The API is unavailable.");
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    void Promise.all([api.health(), api.sources(), api.changes()])
      .then(([nextHealth, nextSources, nextChanges]) => {
        if (cancelled) return;
        setHealth(nextHealth);
        setSources(nextSources);
        setChanges(nextChanges);
        setConnectionError(null);
      })
      .catch((caught: unknown) => {
        if (cancelled) return;
        setConnectionError(caught instanceof Error ? caught.message : "The API is unavailable.");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function runAction(name: string, action: () => Promise<string>) {
    setBusy(name);
    setNotice(null);
    try {
      setNotice(await action());
      await loadDashboard();
    } catch (caught) {
      setNotice(caught instanceof Error ? caught.message : "The operation could not be completed.");
    } finally {
      setBusy(null);
    }
  }

  const sourcesReady = sources.some((source) => source.status === "ready" && source.chunk_count > 0);

  return (
    <main>
      <header className="site-header">
        <a className="brand" href="#top" aria-label="EDB Agent home">
          <span className="brand-mark">E</span>
          <span><strong>EDB Agent</strong><small>Primary education monitor</small></span>
        </a>
        <div className="header-status">
          <StatusPill tone={connectionError ? "error" : "good"}>{connectionError ? "API offline" : "API connected"}</StatusPill>
          <a href="https://www.edb.gov.hk/tc/edu-system/primary-secondary/primary.html" rel="noreferrer" target="_blank">
            View seed source <ArrowIcon size={15} />
          </a>
        </div>
      </header>

      <div className="page-shell" id="top">
        <section className="hero">
          <div>
            <p className="eyebrow">Unofficial proof of concept</p>
            <h1>Answers with evidence.<br /><span>Updates without noise.</span></h1>
          </div>
          <p className="hero-copy">
            A controlled agent for public Hong Kong Education Bureau pages. It searches a local source cache, cites what it uses, and reports meaningful text changes.
          </p>
        </section>

        {connectionError ? (
          <div className="connection-banner" role="alert">
            <strong>FastAPI is not reachable.</strong>
            <span>{connectionError} Start the backend on port 8000, then reload this page.</span>
          </div>
        ) : null}

        <div className="dashboard-grid">
          <AskPanel onAsk={api.ask} sourcesReady={sourcesReady} />
          <SourcesPanel
            busy={busy === "bootstrap"}
            health={health}
            onBootstrap={() => runAction("bootstrap", async () => {
              const result = await api.bootstrap();
              setLatestResults(result.results);
              return `Baseline created for ${result.results.filter((item) => item.status !== "failed").length} page(s).`;
            })}
            sources={sources}
          />
          <UpdatesPanel
            busy={busy}
            changes={changes}
            latestResults={latestResults}
            notice={notice}
            onMutate={() => runAction("mutate", async () => (await api.mutateDemo()).detail)}
            onRefresh={() => runAction("refresh", async () => {
              const result = await api.refresh(true);
              setLatestResults(result.results);
              return result.changes.length
                ? `${result.changes.length} meaningful change(s) detected.`
                : "Check complete. No meaningful text changes detected.";
            })}
            onTestWebhook={() => runAction("webhook", async () => (await api.testWebhook()).detail)}
            sourcesReady={sourcesReady}
            webhookConfigured={health?.webhook_configured ?? false}
          />
        </div>

        <footer className="site-footer">
          <span>This service is not affiliated with the Education Bureau.</span>
          <span>Public sources only · Cached politely · No personal data</span>
        </footer>
      </div>
    </main>
  );
}
