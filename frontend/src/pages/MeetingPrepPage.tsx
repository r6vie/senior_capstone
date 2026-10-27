import {
  ArrowLeft, ArrowRight, BookOpenText, CheckCircle2, Clock3, MessageCircleQuestion,
  RefreshCw, Send, ShieldCheck, Sparkles, Target, UsersRound,
} from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ApiError, api } from "../api";
import { useAuth } from "../auth";
import type { MeetingBrief, PracticeFeedback, ProfileAnswer } from "../types";

const DEFAULT_GOAL = "prepare for a productive conversation and learn from their experience";

export function MeetingPrepPage() {
  const { profileId = "" } = useParams();
  const { token } = useAuth();
  const [goal, setGoal] = useState(DEFAULT_GOAL);
  const [brief, setBrief] = useState<MeetingBrief | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [question, setQuestion] = useState("");
  const [asking, setAsking] = useState(false);
  const [answer, setAnswer] = useState<ProfileAnswer | null>(null);
  const [practiceQuestion, setPracticeQuestion] = useState("");
  const [practiceAnswer, setPracticeAnswer] = useState("");
  const [practiceTurn, setPracticeTurn] = useState(0);
  const [feedback, setFeedback] = useState<PracticeFeedback | null>(null);
  const [coaching, setCoaching] = useState(false);
  const [activeTab, setActiveTab] = useState<"brief" | "ask" | "practice">("brief");

  async function loadBrief(nextGoal: string) {
    if (!token || !profileId) return;
    setLoading(true); setError("");
    try {
      const result = await api.meetingBrief(token, profileId, nextGoal);
      setBrief(result);
      setPracticeQuestion(result.conversation_starters[0] ?? "What would you like to learn from this meeting?");
      setAnswer(null); setFeedback(null); setPracticeTurn(0); setPracticeAnswer("");
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Unable to build this meeting brief.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { void loadBrief(DEFAULT_GOAL); }, [token, profileId]);

  function refresh(event: FormEvent) {
    event.preventDefault();
    void loadBrief(goal);
  }

  async function ask(event: FormEvent) {
    event.preventDefault();
    if (!token || !question.trim()) return;
    setAsking(true); setError("");
    try {
      setAnswer(await api.askProfile(token, profileId, goal, question));
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Unable to answer that question.");
    } finally {
      setAsking(false);
    }
  }

  async function practice(event: FormEvent) {
    event.preventDefault();
    if (!token || !practiceAnswer.trim()) return;
    setCoaching(true); setError("");
    try {
      const result = await api.practiceMeeting(token, profileId, goal, practiceAnswer, practiceTurn);
      setFeedback(result);
      setPracticeQuestion(result.next_question);
      setPracticeTurn((value) => value + 1);
      setPracticeAnswer("");
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Unable to review that answer.");
    } finally {
      setCoaching(false);
    }
  }

  if (loading && !brief) return <div className="loading-panel"><span className="spinner" />Building your meeting brief…</div>;

  return (
    <div className="page-wrap prep-page">
      <Link className="back-link" to="/app/matches"><ArrowLeft size={17} /> Back to matches</Link>
      {error && <div className="state-card state-card--error" role="alert">{error}</div>}

      {brief && (
        <>
          <header className="prep-header">
            <div className="prep-header__person">
              <span className="prep-person__mark">{brief.profile.name.split(/\s+/).slice(0, 2).map((word) => word[0]).join("")}</span>
              <div>
                <span className="eyebrow eyebrow--blue">Meeting prep</span>
                <h1>{brief.profile.name}</h1>
                <p>{brief.headline}{brief.profile.location ? ` · ${brief.profile.location}` : ""}</p>
              </div>
            </div>
            <div className="prep-grounded">
              <ShieldCheck />
              <div><strong>Profile-grounded</strong><span>Based on member-provided information</span></div>
            </div>
          </header>

          <form className="prep-goal" onSubmit={refresh}>
            <Target />
            <label><span>Your goal</span><input aria-label="Meeting goal" value={goal} onChange={(event) => setGoal(event.target.value)} minLength={3} maxLength={500} /></label>
            <button className="prep-goal__button" disabled={loading}><RefreshCw size={15} /> Update</button>
          </form>

          <nav className="prep-tabs" aria-label="Meeting preparation tools" role="tablist">
            <button type="button" role="tab" aria-selected={activeTab === "brief"} className={activeTab === "brief" ? "is-active" : ""} onClick={() => setActiveTab("brief")}><BookOpenText /> Brief</button>
            <button type="button" role="tab" aria-selected={activeTab === "ask"} className={activeTab === "ask" ? "is-active" : ""} onClick={() => setActiveTab("ask")}><MessageCircleQuestion /> Ask profile</button>
            <button type="button" role="tab" aria-selected={activeTab === "practice"} className={activeTab === "practice" ? "is-active" : ""} onClick={() => setActiveTab("practice")}><Sparkles /> Practice</button>
          </nav>

          {activeTab === "brief" && (
            <section className="prep-brief" role="tabpanel">
              <article className="prep-brief__story">
                <span className="eyebrow eyebrow--blue">At a glance</span>
                <h2>Know the person</h2>
                <p className="prep-story__overview">{brief.overview}</p>
                <div className="prep-timeline">
                  {brief.timeline.map((entry, index) => (
                    <div className="prep-timeline__entry" key={`${entry.title}-${index}`}>
                      <span>{entry.marker}</span><div><h3>{entry.title}</h3><p>{entry.detail}</p><small>{entry.source}</small></div>
                    </div>
                  ))}
                </div>
              </article>

              <aside className="prep-brief__aside">
                <section className="prep-summary-section">
                  <div className="prep-summary-section__title"><UsersRound /><h3>Common ground</h3></div>
                  {brief.shared_ground.length ? <ul className="prep-checklist">{brief.shared_ground.map((item) => <li key={item}><CheckCircle2 />{item}</li>)}</ul> : <p className="prep-empty">Your shared CWRU community is a natural opening.</p>}
                </section>
                <section className="prep-summary-section">
                  <div className="prep-summary-section__title"><Clock3 /><h3>25-minute plan</h3></div>
                  <ol className="prep-agenda">{brief.agenda.map((item) => <li key={item}>{item}</li>)}</ol>
                </section>
                <section className="prep-summary-section">
                  <h3>Good questions to ask</h3>
                  <div className="prep-starters">{brief.conversation_starters.slice(0, 3).map((item) => <button type="button" key={item} onClick={() => { setQuestion(item); setActiveTab("ask"); }}>{item}<ArrowRight /></button>)}</div>
                </section>
              </aside>
            </section>
          )}

          {activeTab === "ask" && (
            <section className="prep-workspace" role="tabpanel">
              <div className="prep-workspace__intro"><MessageCircleQuestion /><div><span className="eyebrow eyebrow--blue">Ask this profile</span><h2>What would you like to know?</h2><p>Answers use only information the member added to FoundersCircle.</p></div></div>
              <div className="prep-suggestions">{brief.conversation_starters.slice(0, 3).map((item) => <button type="button" key={item} onClick={() => setQuestion(item)}>{item}</button>)}</div>
              <form className="prep-ask-form" onSubmit={ask}><input value={question} onChange={(event) => setQuestion(event.target.value)} placeholder={`Ask about ${brief.profile.name.split(" ")[0]}’s experience…`} minLength={3} maxLength={500} required /><button className="button button--primary" disabled={asking}>{asking ? "Checking…" : <><Send size={16} /> Ask</>}</button></form>
              {answer && <div className="profile-answer"><Sparkles /><div><p>{answer.answer}</p>{answer.evidence.map((item) => <small key={item.label}><strong>{item.label}:</strong> {item.value}</small>)}</div></div>}
            </section>
          )}

          {activeTab === "practice" && (
            <section className="prep-workspace" role="tabpanel">
              <div className="prep-workspace__intro"><Sparkles /><div><span className="eyebrow eyebrow--blue">Practice coach</span><h2>Rehearse the conversation</h2><p>Practice a response, then get concise feedback before your meeting.</p></div></div>
              <div className="practice-disclaimer">Profile-based practice—not the alumnus and not a prediction of their response.</div>
              <div className="practice-prompt"><span>Coach asks</span><p>{practiceQuestion}</p></div>
              <form className="prep-practice-form" onSubmit={practice}><textarea value={practiceAnswer} onChange={(event) => setPracticeAnswer(event.target.value)} placeholder="Say what you would say in the meeting…" rows={5} maxLength={2000} required /><button className="button button--primary" disabled={coaching}>{coaching ? "Reviewing…" : <>Get coaching <ArrowRight size={16} /></>}</button></form>
              {feedback && <div className="practice-feedback"><p>{feedback.feedback}</p><div><strong>Working well</strong>{feedback.strengths.map((item) => <span key={item}><CheckCircle2 />{item}</span>)}</div><div><strong>Try next</strong>{feedback.suggestions.map((item) => <span key={item}><Target />{item}</span>)}</div></div>}
            </section>
          )}

          <footer className="prep-notice"><ShieldCheck /><span>{brief.grounding_notice}</span></footer>
        </>
      )}
    </div>
  );
}
