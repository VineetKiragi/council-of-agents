import { useState, useEffect, useRef } from "react";
import "./App.css";
import { startDeliberation, getSessions, getSession } from "./services/api";
import SubmitPanel from "./components/SubmitPanel";
import DeliberationView from "./components/DeliberationView";
import ResultPanel from "./components/ResultPanel";

export default function App() {
  const [currentSession, setCurrentSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [pastSessions, setPastSessions] = useState([]);
  const [deliberating, setDeliberating] = useState(false);
  const [error, setError] = useState(null);

  const wsRef = useRef(null);

  useEffect(() => {
    getSessions()
      .then(setPastSessions)
      .catch((err) => setError(err.message));

    // Close any open WS on unmount
    return () => wsRef.current?.close();
  }, []);

  function handleSubmit(prompt) {
    // Close any previous connection
    wsRef.current?.close();

    setError(null);
    setMessages([]);
    setCurrentSession(null);
    setDeliberating(true);

    // Return a Promise so SubmitPanel's "Thinking…" spans the full deliberation
    return new Promise((resolve) => {
      wsRef.current = startDeliberation(
        prompt,

        // onMessage — append each arriving agent response
        (msg) => setMessages((prev) => [...prev, msg]),

        // onComplete — fetch the finished session for ResultPanel + refresh sidebar
        async (data) => {
          setDeliberating(false);
          try {
            const session = await getSession(data.session_id);
            setCurrentSession(session);
            setPastSessions((prev) => [
              session,
              ...prev.filter((s) => s.id !== session.id),
            ]);
          } catch (err) {
            setError(err.message);
          }
          resolve();
        },

        // onError
        (data) => {
          setDeliberating(false);
          setError(data.detail || "Deliberation failed");
          resolve();
        },
      );
    });
  }

  async function handleSelectSession(sessionId) {
    // Close any running deliberation
    wsRef.current?.close();
    setDeliberating(false);
    setError(null);

    try {
      const session = await getSession(sessionId);
      setCurrentSession(session);
      setMessages(session.messages ?? []);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <>
      <aside className="app-sidebar">
        <h2>Past sessions</h2>
        {pastSessions.length === 0 && (
          <p style={{ margin: 0, fontSize: "0.82rem", color: "#aaa" }}>None yet</p>
        )}
        {pastSessions.map((s) => (
          <button
            key={s.id}
            className={`session-item${currentSession?.id === s.id ? " active" : ""}`}
            onClick={() => handleSelectSession(s.id)}
          >
            <span className="session-item-prompt">{s.prompt}</span>
            <span className="session-item-meta">{s.status}</span>
          </button>
        ))}
      </aside>

      <main className="app-main">
        <h1>Council of Agents</h1>

        <SubmitPanel onSubmit={handleSubmit} />

        {deliberating && (
          <p className="deliberating-indicator">Deliberation in progress…</p>
        )}

        {error && <p className="error-text">{error}</p>}

        {(messages.length > 0 || currentSession) && (
          <>
            <DeliberationView messages={messages} />
            {currentSession && <ResultPanel session={currentSession} />}
          </>
        )}
      </main>
    </>
  );
}
