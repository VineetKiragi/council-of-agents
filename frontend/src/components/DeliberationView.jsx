import { useEffect, useRef } from "react";

const ROUND_LABEL = {
  1: "Round 1: Initial Positions",
  2: "Round 2: Critique & Discussion",
  3: "Round 3: Final Positions",
  0: "Chairman's Synthesis",
};

const STATUS_COLOR = {
  pending: "#888",
  in_progress: "#f0a500",
  completed: "#4caf50",
  failed: "#e53935",
};

export default function DeliberationView({ messages }) {
  const bottomRef = useRef(null);

  // Auto-scroll to the latest message whenever a new one arrives
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length]);

  if (messages.length === 0) {
    return <p style={styles.empty}>Waiting for agents…</p>;
  }

  // Group by round_number; display rounds 1→2→3→0 (chairman last)
  const byRound = {};
  for (const msg of messages) {
    (byRound[msg.round_number] ??= []).push(msg);
  }
  const roundOrder = Object.keys(byRound)
    .map(Number)
    .sort((a, b) => (a === 0 ? 1 : b === 0 ? -1 : a - b));

  return (
    <div style={styles.wrapper}>
      {roundOrder.map((roundNum) => (
        <div key={roundNum} style={styles.roundSection}>
          <div style={styles.roundHeader}>
            <span style={styles.roundLabel}>
              {ROUND_LABEL[roundNum] ?? `Round ${roundNum}`}
            </span>
          </div>
          <div style={styles.thread}>
            {byRound[roundNum].map((msg) => (
              <MessageCard key={msg.id ?? `${msg.agent_pseudonym}-${roundNum}`} message={msg} />
            ))}
          </div>
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  );
}

function MessageCard({ message }) {
  const { agent_pseudonym, agent_role, agent_provider, round_number, content } = message;

  const isChairman = round_number === 0;

  const subtitle = [agent_role, agent_provider].filter(Boolean).join(" · ");

  return (
    <div
      className="message-card"
      style={{ ...styles.card, ...(isChairman ? styles.chairmanCard : {}) }}
    >
      <div style={styles.cardHeader}>
        <span style={{ ...styles.pseudonym, ...(isChairman ? styles.chairmanPseudonym : {}) }}>
          {agent_pseudonym}
        </span>
        {subtitle && <span style={styles.subtitle}>{subtitle}</span>}
      </div>
      <p style={styles.content}>{content}</p>
    </div>
  );
}

const styles = {
  wrapper: {
    display: "flex",
    flexDirection: "column",
    gap: "1.75rem",
    width: "100%",
    maxWidth: "640px",
  },
  roundSection: {
    display: "flex",
    flexDirection: "column",
    gap: "0.75rem",
  },
  roundHeader: {
    display: "flex",
    alignItems: "center",
    gap: "0.75rem",
  },
  roundLabel: {
    fontSize: "0.78rem",
    fontWeight: 700,
    textTransform: "uppercase",
    letterSpacing: "0.06em",
    color: "#646cff",
  },
  thread: {
    display: "flex",
    flexDirection: "column",
    gap: "0.65rem",
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
  chairmanCard: {
    border: "1px solid #646cff",
    backgroundColor: "#f5f4ff",
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
  chairmanPseudonym: {
    color: "#4f46e5",
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
};
