import { useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const ROUND_LABEL = {
  1: "Round 1: Initial Positions",
  2: "Round 2: Critique & Discussion",
  3: "Round 3: Final Positions",
  0: "Chairman's Synthesis",
};

// Provider badge colours: light background, darker text
const PROVIDER_STYLE = {
  anthropic: { backgroundColor: "#dbeafe", color: "#1e40af", label: "Anthropic" },
  openai:    { backgroundColor: "#dcfce7", color: "#166534", label: "OpenAI" },
  google:    { backgroundColor: "#ffedd5", color: "#9a3412", label: "Google" },
};

export default function DeliberationView({ messages, revealMap }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length]);

  if (messages.length === 0) {
    return <p style={styles.empty}>Waiting for agents…</p>;
  }

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
              <MessageCard
                key={msg.id ?? `${msg.agent_pseudonym}-${roundNum}`}
                message={msg}
                reveal={revealMap?.[msg.agent_pseudonym] ?? null}
              />
            ))}
          </div>
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  );
}

function MessageCard({ message, reveal }) {
  const { agent_pseudonym, round_number, content } = message;
  const isChairman = round_number === 0;

  // If revealed, show "Agent A — Analytical (OpenAI)"
  // If not yet revealed, show just the pseudonym
  const roleLabel = reveal ? `${agent_pseudonym} — ${reveal.role}` : agent_pseudonym;
  const providerStyle = reveal ? (PROVIDER_STYLE[reveal.provider] ?? null) : null;

  return (
    <div
      className="message-card"
      style={{ ...styles.card, ...(isChairman ? styles.chairmanCard : {}) }}
    >
      <div style={styles.cardHeader}>
        <span style={{ ...styles.pseudonym, ...(isChairman ? styles.chairmanPseudonym : {}) }}>
          {roleLabel}
        </span>
        {providerStyle && (
          <span style={{ ...styles.providerBadge, ...providerStyle }}>
            {providerStyle.label}
          </span>
        )}
      </div>
      <div className="md-content">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
      </div>
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
    alignItems: "center",
    gap: "0.6rem",
    marginBottom: "0.5rem",
    flexWrap: "wrap",
  },
  pseudonym: {
    fontWeight: 700,
    fontSize: "0.95rem",
    color: "#213547",
  },
  chairmanPseudonym: {
    color: "#4f46e5",
  },
  providerBadge: {
    fontSize: "0.7rem",
    fontWeight: 600,
    padding: "0.15em 0.55em",
    borderRadius: "10px",
    letterSpacing: "0.03em",
  },
};
