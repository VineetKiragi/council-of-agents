import { useState } from "react";

export default function SubmitPanel({ onSubmit }) {
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    const trimmed = prompt.trim();
    if (!trimmed) return;

    setLoading(true);
    try {
      await onSubmit(trimmed);
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} style={styles.form}>
      <textarea
        style={styles.textarea}
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder="Ask the council a question…"
        rows={4}
        disabled={loading}
      />
      <button type="submit" className="submit-btn" disabled={loading || !prompt.trim()}>
        {loading ? "Thinking…" : "Submit"}
      </button>
    </form>
  );
}

const styles = {
  form: {
    display: "flex",
    flexDirection: "column",
    gap: "0.75rem",
    width: "100%",
    maxWidth: "640px",
  },
  textarea: {
    width: "100%",
    padding: "0.75rem",
    fontSize: "1rem",
    fontFamily: "inherit",
    lineHeight: "1.5",
    borderRadius: "8px",
    border: "1px solid #d0d0d0",
    backgroundColor: "#fff",
    color: "#213547",
    resize: "vertical",
    boxSizing: "border-box",
    outline: "none",
  },
};
