const STATUS_LABEL = {
  pending: "Pending",
  in_progress: "In progress",
  completed: "Completed",
  failed: "Failed",
};

const STATUS_COLOR = {
  pending: "#888",
  in_progress: "#f0a500",
  completed: "#4caf50",
  failed: "#e53935",
};

export default function DeliberationView({ session }) {
  const { prompt, status, final_decision, messages } = session;

  return (
    <div style={styles.wrapper}>
      <div style={styles.header}>
        <p style={styles.prompt}>{prompt}</p>
        <span style={{ ...styles.statusBadge, backgroundColor: STATUS_COLOR[status] ?? "#888" }}>
          {STATUS_LABEL[status] ?? status}
        </span>
      </div>

      <div style={styles.thread}>
        {messages.length === 0 ? (
          <p style={styles.empty}>Waiting for agents…</p>
        ) : (
          messages.map((msg) => <MessageCard key={msg.id} message={msg} />)
        )}
      </div>

      {final_decision && (
        <div style={styles.finalDecision}>
          <p style={styles.finalLabel}>Final decision</p>
          <p style={styles.finalContent}>{final_decision}</p>
        </div>
      )}
    </div>
  );
}

function MessageCard({ message }) {
  const { agent_pseudonym, agent_role, agent_provider, round_number, content } = message;

  const subtitle = [
    round_number === 0 ? "synthesis" : `round ${round_number}`,
    agent_role,
    agent_provider,
  ]
    .filter(Boolean)
    .join(" · ");

  return (
    <div style={styles.card}>
      <div style={styles.cardHeader}>
        <span style={styles.pseudonym}>{agent_pseudonym}</span>
        <span style={styles.subtitle}>{subtitle}</span>
      </div>
      <p style={styles.content}>{content}</p>
    </div>
  );
}

const styles = {
  wrapper: {
    display: "flex",
    flexDirection: "column",
    gap: "1.25rem",
    width: "100%",
    maxWidth: "640px",
  },
  header: {
    display: "flex",
    alignItems: "flex-start",
    justifyContent: "space-between",
    gap: "1rem",
  },
  prompt: {
    margin: 0,
    fontStyle: "italic",
    color: "#555",
    flex: 1,
  },
  statusBadge: {
    flexShrink: 0,
    padding: "0.2em 0.7em",
    borderRadius: "12px",
    fontSize: "0.78rem",
    fontWeight: 600,
    color: "#fff",
    textTransform: "uppercase",
    letterSpacing: "0.04em",
  },
  thread: {
    display: "flex",
    flexDirection: "column",
    gap: "0.75rem",
  },
  empty: {
    margin: 0,
    color: "#aaa",
    fontStyle: "italic",
  },
  card: {
    padding: "0.85rem 1rem",
    borderRadius: "8px",
    backgroundColor: "#fff",
    border: "1px solid #e0e0e0",
    boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
  },
  cardHeader: {
    display: "flex",
    alignItems: "baseline",
    gap: "0.6rem",
    marginBottom: "0.5rem",
  },
  pseudonym: {
    fontWeight: 700,
    fontSize: "0.95rem",
    color: "#213547",
  },
  subtitle: {
    fontSize: "0.78rem",
    color: "#999",
  },
  content: {
    margin: 0,
    lineHeight: 1.6,
    color: "#213547",
    whiteSpace: "pre-wrap",
  },
  finalDecision: {
    padding: "1rem",
    borderRadius: "8px",
    border: "1px solid #4caf50",
    backgroundColor: "#f2faf2",
  },
  finalLabel: {
    margin: "0 0 0.4rem",
    fontSize: "0.78rem",
    fontWeight: 700,
    textTransform: "uppercase",
    letterSpacing: "0.06em",
    color: "#2e7d32",
  },
  finalContent: {
    margin: 0,
    lineHeight: 1.6,
    color: "#213547",
    whiteSpace: "pre-wrap",
  },
};
