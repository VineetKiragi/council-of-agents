import { useState, useEffect, useRef } from "react";
import "./App.css";
import {
  startDeliberation,
  getSessions,
  getSession,
  revealSession,
  getSessionStats,
} from "./services/api";
import SubmitPanel from "./components/SubmitPanel";
import DeliberationView from "./components/DeliberationView";
import StatsPanel from "./components/StatsPanel";

export default function App() {
  const [currentSession, setCurrentSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [pastSessions, setPastSessions] = useState([]);
  const [deliberating, setDeliberating] = useState(false);
  const [error, setError] = useState(null);

  // Reveal & stats state
  const [revealMap, setRevealMap] = useState(null); // pseudonym → {role, provider}
  const [stats, setStats] = useState(null);

  const wsRef = useRef(null);

  useEffect(() => {
    getSessions()
      .then(setPastSessions)
      .catch((err) => setError(err.message));

    return () => wsRef.current?.close();
  }, []);

  function handleSubmit(prompt) {
    wsRef.current?.close();
    setError(null);
    setMessages([]);
    setCurrentSession(null);
    setRevealMap(null);
    setStats(null);
    setDeliberating(true);

    return new Promise((resolve) => {
      wsRef.current = startDeliberation(
        prompt,
        (msg) => setMessages((prev) => [...prev, msg]),
        async (data) => {
          setDeliberating(false);
          try {
            const [session, statsData] = await Promise.all([
              getSession(data.session_id),
              getSessionStats(data.session_id),
            ]);
            setCurrentSession(session);
            setStats(statsData);
            setPastSessions((prev) => [
              session,
              ...prev.filter((s) => s.id !== session.id),
            ]);
          } catch (err) {
            setError(err.message);
          }
          resolve();
        },
        (data) => {
          setDeliberating(false);
          setError(data.detail || "Deliberation failed");
          resolve();
        },
      );
    });
  }

  async function handleSelectSession(sessionId) {
    wsRef.current?.close();
    setDeliberating(false);
    setError(null);
    setRevealMap(null);
    setStats(null);

    try {
      const session = await getSession(sessionId);
      setCurrentSession(session);
      setMessages(session.messages ?? []);
      if (session.status === "completed") {
        const statsData = await getSessionStats(sessionId);
        setStats(statsData);
      }
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleReveal() {
    if (!currentSession) return;
    try {
      const data = await revealSession(currentSession.id);
      const map = {};
      for (const msg of data.messages) {
        map[msg.agent_pseudonym] = {
          role: msg.agent_role,
          provider: msg.agent_provider,
        };
      }
      setRevealMap(map);
    } catch (err) {
      setError(err.message);
    }
  }

  const isCompleted = currentSession?.status === "completed";
  const canReveal = isCompleted && !revealMap && !deliberating;

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
            <DeliberationView messages={messages} revealMap={revealMap} />

            {canReveal && (
              <button className="reveal-btn" onClick={handleReveal}>
                Reveal Agents
              </button>
            )}
            {revealMap && (
              <p className="revealed-indicator">Agent identities revealed</p>
            )}

            <StatsPanel stats={stats} />
          </>
        )}
      </main>
    </>
  );
}
