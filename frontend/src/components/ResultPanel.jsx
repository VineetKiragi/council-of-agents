export default function ResultPanel({ session }) {
  if (!session.final_decision) {
    return <p style={styles.pending}>Decision pending…</p>;
  }

  return (
    <div style={styles.wrapper}>
      <p style={styles.label}>Council decision</p>
      <p style={styles.decision}>{session.final_decision}</p>
    </div>
  );
}

const styles = {
  pending: {
    margin: 0,
    color: "#aaa",
    fontStyle: "italic",
    fontSize: "0.9rem",
  },
  wrapper: {
    width: "100%",
    maxWidth: "640px",
    padding: "1.25rem",
    borderRadius: "8px",
    border: "1px solid #646cff",
    backgroundColor: "#f5f4ff",
  },
  label: {
    margin: "0 0 0.5rem",
    fontSize: "0.78rem",
    fontWeight: 700,
    textTransform: "uppercase",
    letterSpacing: "0.06em",
    color: "#4f46e5",
  },
  decision: {
    margin: 0,
    lineHeight: 1.7,
    fontSize: "1.05rem",
    color: "#213547",
    whiteSpace: "pre-wrap",
  },
};
