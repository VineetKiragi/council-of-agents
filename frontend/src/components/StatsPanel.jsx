const PROVIDER_LABEL = { anthropic: "Anthropic", openai: "OpenAI", google: "Google" };

const ROUND_LABEL = {
  1: "Round 1",
  2: "Round 2",
  3: "Round 3",
  0: "Chairman",
};

export default function StatsPanel({ stats }) {
  if (!stats) return null;

  const costStr = `$${stats.estimated_cost.toFixed(4)}`;
  const agentTimeStr = `${(stats.total_latency_ms / 1000).toFixed(1)}s`;

  return (
    <details style={styles.details}>
      <summary style={styles.summary}>Session Stats</summary>

      <div style={styles.body}>
        {/* Top-line numbers */}
        <div style={styles.topRow}>
          <Stat label="Total tokens" value={stats.total_tokens.toLocaleString()} />
          <Stat label="Est. cost" value={costStr} />
          <Stat label="Agent time" value={agentTimeStr} />
        </div>

        {/* Per-agent breakdown */}
        <p style={styles.sectionLabel}>Per agent</p>
        <table style={styles.table}>
          <thead>
            <tr>
              {["Agent", "Role", "Provider", "Tokens", "Messages", "Avg latency"].map((h) => (
                <th key={h} style={styles.th}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {stats.per_agent.map((a) => (
              <tr key={a.pseudonym}>
                <td style={styles.td}>{a.pseudonym}</td>
                <td style={styles.td}>{a.role}</td>
                <td style={styles.td}>{PROVIDER_LABEL[a.provider] ?? a.provider}</td>
                <td style={styles.td}>{a.total_tokens?.toLocaleString() ?? "—"}</td>
                <td style={styles.td}>{a.num_messages}</td>
                <td style={styles.td}>
                  {a.num_messages > 0
                    ? `${Math.round(a.total_latency_ms / a.num_messages).toLocaleString()} ms`
                    : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {/* Per-round breakdown */}
        <p style={styles.sectionLabel}>Per round</p>
        <table style={styles.table}>
          <thead>
            <tr>
              {["Round", "Tokens", "Messages", "Total latency"].map((h) => (
                <th key={h} style={styles.th}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {stats.per_round.map((r) => (
              <tr key={r.round_number}>
                <td style={styles.td}>{ROUND_LABEL[r.round_number] ?? `Round ${r.round_number}`}</td>
                <td style={styles.td}>{r.total_tokens?.toLocaleString() ?? "—"}</td>
                <td style={styles.td}>{r.num_messages}</td>
                <td style={styles.td}>{r.total_latency_ms?.toLocaleString()} ms</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </details>
  );
}

function Stat({ label, value }) {
  return (
    <div style={styles.statBox}>
      <span style={styles.statLabel}>{label}</span>
      <span style={styles.statValue}>{value}</span>
    </div>
  );
}

const styles = {
  details: {
    width: "100%",
    maxWidth: "640px",
    borderRadius: "8px",
    border: "1px solid #e0e0e0",
    backgroundColor: "#fff",
    overflow: "hidden",
  },
  summary: {
    padding: "0.75rem 1rem",
    cursor: "pointer",
    fontSize: "0.82rem",
    fontWeight: 700,
    textTransform: "uppercase",
    letterSpacing: "0.05em",
    color: "#555",
    userSelect: "none",
    listStyle: "none",
  },
  body: {
    padding: "0 1rem 1rem",
    display: "flex",
    flexDirection: "column",
    gap: "0.75rem",
  },
  topRow: {
    display: "flex",
    gap: "1rem",
  },
  statBox: {
    flex: 1,
    padding: "0.6rem 0.75rem",
    borderRadius: "6px",
    backgroundColor: "#f5f5f5",
    display: "flex",
    flexDirection: "column",
    gap: "0.2rem",
  },
  statLabel: {
    fontSize: "0.7rem",
    textTransform: "uppercase",
    letterSpacing: "0.05em",
    color: "#888",
  },
  statValue: {
    fontSize: "1rem",
    fontWeight: 700,
    color: "#213547",
  },
  sectionLabel: {
    margin: "0.25rem 0 0",
    fontSize: "0.72rem",
    fontWeight: 700,
    textTransform: "uppercase",
    letterSpacing: "0.05em",
    color: "#aaa",
  },
  table: {
    width: "100%",
    borderCollapse: "collapse",
    fontSize: "0.82rem",
  },
  th: {
    textAlign: "left",
    padding: "0.3rem 0.5rem",
    borderBottom: "1px solid #e0e0e0",
    color: "#888",
    fontWeight: 600,
    fontSize: "0.72rem",
    textTransform: "uppercase",
    letterSpacing: "0.04em",
  },
  td: {
    padding: "0.35rem 0.5rem",
    borderBottom: "1px solid #f0f0f0",
    color: "#213547",
  },
};
