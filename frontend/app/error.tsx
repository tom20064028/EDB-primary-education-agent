"use client";

export default function ErrorPage({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <main className="fatal-error">
      <p className="eyebrow">Application error</p>
      <h1>Something went wrong</h1>
      <p>The dashboard could not finish loading. The source cache has not been changed.</p>
      <button className="button button-primary" onClick={reset} type="button">
        Try again
      </button>
    </main>
  );
}

