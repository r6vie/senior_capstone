import { CheckCircle2, MessageCircle, RotateCcw, Send, Sparkles } from "lucide-react";
import { FormEvent, KeyboardEvent, useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ApiError, api } from "../api";
import { useAuth } from "../auth";
import { CoverageMeter, FactList } from "../components/Facts";
import type { ChatMessage, Fact, FactEdit, InterviewTurn } from "../types";

export function InterviewPage() {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [turn, setTurn] = useState<InterviewTurn | null>(null);
  const [pending, setPending] = useState<ChatMessage | null>(null);
  const [draft, setDraft] = useState("");
  const [thinking, setThinking] = useState(false);
  const [error, setError] = useState("");
  const [tab, setTab] = useState<"chat" | "facts">("chat");
  const endRef = useRef<HTMLDivElement>(null);

  const fail = useCallback((caught: unknown, fallback: string) => {
    if (caught instanceof ApiError && caught.status === 409 && caught.message.includes("basics")) {
      navigate("/onboarding", { replace: true });
      return;
    }
    setError(caught instanceof ApiError ? caught.message : fallback);
  }, [navigate]);

  const begin = useCallback(async () => {
    if (!token) return;
    setThinking(true);
    setError("");
    try { setTurn(await api.startInterview(token)); }
    catch (caught) { fail(caught, "Unable to start the interview."); }
    finally { setThinking(false); }
  }, [token, fail]);

  useEffect(() => {
    if (!token) return;
    api.currentInterview(token)
      .then(setTurn)
      .catch((caught) => {
        if (caught instanceof ApiError && caught.status === 404) void begin();
        else fail(caught, "Unable to load your interview.");
      });
  }, [token, begin, fail]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [turn?.interview.messages.length, pending, thinking]);

  async function send(event?: FormEvent) {
    event?.preventDefault();
    const text = draft.trim();
    if (!token || !turn || !text || thinking) return;
    setPending({ role: "member", text, at: new Date().toISOString() });
    setDraft("");
    setThinking(true);
    setError("");
    try {
      setTurn(await api.answerInterview(token, turn.interview.session_id, text));
    } catch (caught) {
      setDraft(text);
      fail(caught, "Your answer didn't go through. Try again.");
    } finally {
      setPending(null);
      setThinking(false);
    }
  }

  function keyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault();
      void send();
    }
  }

  async function finish() {
    if (!token || !turn) return;
    try { setTurn(await api.finishInterview(token, turn.interview.session_id)); }
    catch (caught) { fail(caught, "Unable to finish the interview."); }
  }

  async function refreshCoverage() {
    if (!token) return;
    const status = await api.onboardingStatus(token);
    setTurn((current) => current && { ...current, coverage: status.coverage });
  }

  async function editFact(fact: Fact, edit: FactEdit) {
    if (!token) return;
    try {
      const updated = await api.editFact(token, fact.id, edit);
      setTurn((current) => current && { ...current, facts: current.facts.map((item) => (item.id === fact.id ? updated : item)) });
      await refreshCoverage();
    } catch (caught) { fail(caught, "Unable to update that fact."); }
  }

  async function deleteFact(fact: Fact) {
    if (!token) return;
    try {
      await api.deleteFact(token, fact.id);
      setTurn((current) => current && { ...current, facts: current.facts.filter((item) => item.id !== fact.id) });
      await refreshCoverage();
    } catch (caught) { fail(caught, "Unable to delete that fact."); }
  }

  if (!turn) {
    return (
      <div className="page-wrap">
        {error ? <div className="state-card state-card--error">{error}</div> : <div className="loading-panel"><span className="spinner" />Starting your conversation…</div>}
      </div>
    );
  }

  const finished = turn.interview.status === "finished";
  const messages = pending ? [...turn.interview.messages, pending] : turn.interview.messages;
  const learned = turn.facts.filter((fact) => fact.source !== "basics_form");
  const unconfirmed = learned.filter((fact) => !fact.confirmed).length;

  return (
    <div className="page-wrap interview-page">
      <div className="onboarding-steps" aria-label="Onboarding progress">
        <Link to="/onboarding" className="onboarding-steps__item onboarding-steps__item--done"><CheckCircle2 size={15} /> The basics</Link>
        <span className="onboarding-steps__item onboarding-steps__item--active">2 · A short conversation</span>
      </div>

      <div className="interview-tabs" role="tablist">
        <button role="tab" aria-selected={tab === "chat"} className={tab === "chat" ? "active" : ""} onClick={() => setTab("chat")}><MessageCircle size={16} /> Conversation</button>
        <button role="tab" aria-selected={tab === "facts"} className={tab === "facts" ? "active" : ""} onClick={() => setTab("facts")}>
          <Sparkles size={16} /> Your facts{unconfirmed > 0 && <span className="count-badge">{unconfirmed}</span>}
        </button>
      </div>

      <div className="interview-layout">
        <section className={`chat ${tab === "chat" ? "" : "pane--hidden"}`} aria-label="Conversation">
          <header className="chat__header">
            <div>
              <h1>Tell us what you're looking for</h1>
              <p>Answer in your own words. Stop whenever you like; you can always come back.</p>
            </div>
            {!finished && <button className="button button--secondary" onClick={finish} disabled={thinking}>Done for now</button>}
          </header>

          <div className="chat__messages" aria-live="polite">
            {messages.map((message, index) => (
              <div key={`${message.at}-${index}`} className={`bubble bubble--${message.role}`}>{message.text}</div>
            ))}
            {thinking && <div className="bubble bubble--assistant bubble--typing" aria-label="Thinking"><span /><span /><span /></div>}
            <div ref={endRef} />
          </div>

          {error && <div className="form-error chat__error" role="alert">{error}</div>}

          {finished ? (
            <div className="chat__finished">
              <p><CheckCircle2 size={18} /> Thanks! Your answers are saved. Review what we learned, or pick up the conversation any time.</p>
              <div>
                <button className="button button--secondary" onClick={() => void begin()} disabled={thinking}><RotateCcw size={16} /> Keep talking</button>
                <Link className="button button--primary" to="/app">Go to the directory</Link>
              </div>
            </div>
          ) : (
            <form className="chat__composer" onSubmit={send}>
              <textarea
                value={draft} onChange={(event) => setDraft(event.target.value)} onKeyDown={keyDown}
                placeholder="Type your answer…" rows={2} maxLength={2000} aria-label="Your answer" disabled={thinking}
              />
              <button className="button button--primary" disabled={thinking || !draft.trim()} aria-label="Send"><Send size={17} /></button>
            </form>
          )}
        </section>

        <aside className={`learned ${tab === "facts" ? "" : "pane--hidden"}`} aria-label="What we've learned">
          <CoverageMeter coverage={turn.coverage} />
          <div className="learned__heading">
            <h2>What we've learned</h2>
            <p>Check each one. Choose who can see it; "Only me" still helps your matches.</p>
          </div>
          <FactList facts={learned} onEdit={editFact} onDelete={deleteFact} empty="Things you share will appear here as we go." />
        </aside>
      </div>
    </div>
  );
}
