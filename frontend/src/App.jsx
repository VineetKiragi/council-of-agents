import { useState, useEffect } from "react";
import "./App.css";
import { createSession, getSessions, getSession } from "./services/api";
import SubmitPanel from "./components/SubmitPanel";
import DeliberationView from "./components/DeliberationView";
import ResultPanel from "./components/ResultPanel";

export default function App() {
  const [currentSession, setCurrentSession] = useState(null);
  const [pastSessions, setPastSessions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    getSessions()
      .then(setPastSessions)
      .catch((err) => setError(err.message));
  }, []);

  async function handleSubmit(prompt) {
    setError(null);
    setLoading(true);
    try {
      const session = await createSession(prompt);
      setCurrentSession(session);
      setPastSessions((prev) => [session, ...prev]);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleSelectSession(sessionId) {
    setError(null);
    try {
      const session = await getSession(sessionId);
      setCurrentSession(session);
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

        {error && <p className="error-text">{error}</p>}

        {currentSession && (
          <>
            <DeliberationView session={currentSession} />
            <ResultPanel session={currentSession} />
          </>
        )}
      </main>
    </>
  );
}
