type StatusPillProps = {
  tone: "good" | "warning" | "neutral" | "error";
  children: React.ReactNode;
};

export function StatusPill({ tone, children }: StatusPillProps) {
  return <span className={`status-pill status-${tone}`}>{children}</span>;
}

