import { ArrowRight, Check, CheckCircle2, ChevronDown, Sparkles } from "lucide-react";
import { FormEvent, KeyboardEvent, useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ApiError, api } from "../api";
import { useAuth } from "../auth";
import { FactCard, FactList } from "../components/Facts";
import type { Fact, FactEdit, InterviewTurn, Question } from "../types";

const AREA_LABELS: Record<Question["area"], string> = {
  needs: "What you need", offers: "What you can offer", style: "How you like to connect",
  background: "Shared background", goals: "Your goals",
};

export function InterviewPage() {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [turn, setTurn] = useState<InterviewTurn | null>(null);
  const [picked, setPicked] = useState<string[]>([]);
  const [detail, setDetail] = useState("");
  const [working, setWorking] = useState(false);
  const [error, setError] = useState("");
  const [showAll, setShowAll] = useState(false);

  const fail = useCallback((caught: unknown, fallback: string) => {
    if (caught instanceof ApiError && caught.status === 409 && caught.message.includes("basics")) {
      navigate("/onboarding", { replace: true });
      return;
    }
    setError(caught instanceof ApiError ? caught.message : fallback);
  }, [navigate]);

  const begin = useCallback(async () => {
    if (!token) return;
    setWorking(true);
    setError("");
    try { setTurn(await api.startInterview(token)); }
    catch (caught) { fail(caught, "Unable to start."); }
    finally { setWorking(false); }
  }, [token, fail]);

  useEffect(() => {
    if (!token) return;
    api.currentInterview(token)
      .then((loaded) => (loaded.interview.status === "finished" || !loaded.interview.question ? begin() : setTurn(loaded)))
      .catch((caught) => {
        if (caught instanceof ApiError && caught.status === 404) void begin();
        else fail(caught, "Unable to load your questions.");
      });
  }, [token, begin, fail]);

  const question = turn?.interview.question ?? null;
  useEffect(() => { setPicked([]); setDetail(""); }, [question?.id]);

  function toggle(choice: string) {
    if (!question) return;
    setPicked((current) => {
      if (current.includes(choice)) return current.filter((item) => item !== choice);
      return question.multiple ? [...current, choice] : [choice];
    });
  }

  async function submit(skipped = false) {
    if (!token || !turn || !question || working) return;
    if (!skipped && !picked.length && !detail.trim()) {
      setError(question.choices.length ? "Pick an answer or add a few words." : "Add a few words, or skip this one.");
      return;
    }
    setWorking(true);
    setError("");
    try {
      const answer = skipped ? { question_id: question.id, choices: [], text: "", skipped: true }
        : { question_id: question.id, choices: picked, text: detail.trim() };
      setTurn(await api.answerInterview(token, turn.interview.session_id, answer));
    } catch (caught) {
      fail(caught, "Your answer didn't go through. Try again.");
    } finally {
      setWorking(false);
    }
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    void submit();
  }

  function keyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) {
      event.preventDefault();
      void submit();
    }
  }

  async function finish() {
    if (!token || !turn) return;
    try { setTurn(await api.finishInterview(token, turn.interview.session_id)); }
    catch (caught) { fail(caught, "Unable to save your progress."); }
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
    } catch (caught) { fail(caught, "Unable to update that."); }
  }

  async function deleteFact(fact: Fact) {
    if (!token) return;
    try {
      await api.deleteFact(token, fact.id);
      setTurn((current) => current && {
        ...current,
        facts: current.facts.filter((item) => item.id !== fact.id),
        interview: { ...current.interview, added: current.interview.added.filter((id) => id !== fact.id) },
      });
      await refreshCoverage();
    } catch (caught) { fail(caught, "Unable to delete that."); }
  }

  if (!turn) {
    return (
      <div className="page-wrap question-page">
        {error ? <div className="state-card state-card--error">{error}</div> : <div className="loading-panel"><span className="spinner" />Getting your first question ready…</div>}
      </div>
    );
  }

  const { interview, coverage } = turn;
  const learned = turn.facts.filter((fact) => fact.source !== "basics_form");
  const added = turn.facts.filter((fact) => interview.added.includes(fact.id));

  if (interview.status === "finished") {
    return (
      <div className="page-wrap question-page">
        <section className="question-card question-card--center">
          <CheckCircle2 className="question-card__icon" />
          <h1 className="question-card__prompt">Your answers are saved.</h1>
          <p className="question-card__lede">Your profile is {coverage.percent}% complete. Pick up where you left off any time.</p>
          <div className="question-card__footer question-card__footer--center">
            <button className="button button--secondary" onClick={() => void begin()} disabled={working}>Keep going</button>
            <Link className="button button--primary" to="/app">Go to the directory</Link>
          </div>
        </section>
      </div>
    );
  }

  return (
    <div className="page-wrap question-page">
      <div className="onboarding-steps" aria-label="Onboarding progress">
        <Link to="/onboarding" className="onboarding-steps__item onboarding-steps__item--done"><CheckCircle2 size={15} /> The basics</Link>
        <span className="onboarding-steps__item onboarding-steps__item--active">2 · A few questions</span>
      </div>

      <div className="question-progress">
        <div className="question-progress__label">
          <span>Profile strength <strong>{coverage.percent}%</strong></span>
          <button className="button button--quiet" onClick={finish} disabled={working}>Done for now</button>
        </div>
        <div className="coverage__bar" role="progressbar" aria-valuenow={coverage.percent} aria-valuemin={0} aria-valuemax={100} aria-label="Profile strength">
          <span style={{ width: `${coverage.percent}%` }} />
        </div>
      </div>

      {interview.done && (
        <div className="question-ready" role="status">
          <Sparkles size={18} />
          <p><strong>Your profile is ready for matching.</strong> More answers make your matches sharper, or <Link to="/app">head to the directory</Link>.</p>
        </div>
      )}

      {question && (
        <form className={`question-card ${working ? "question-card--working" : ""}`} onSubmit={onSubmit} aria-busy={working}>
          <div className="question-card__meta">
            <span className="eyebrow eyebrow--blue">{AREA_LABELS[question.area]}</span>
            <span>Question {interview.answered + 1}</span>
          </div>
          <h1 className="question-card__prompt" key={question.id}>{question.prompt}</h1>

          {question.choices.length > 0 && (
            <div className="question-card__choices" role="group" aria-label={question.multiple ? "Choose any that apply" : "Choose one"}>
              {question.choices.map((choice) => (
                <button
                  type="button" key={choice} aria-pressed={picked.includes(choice)}
                  className={`answer-chip ${picked.includes(choice) ? "answer-chip--on" : ""}`}
                  onClick={() => toggle(choice)} disabled={working}
                >
                  {picked.includes(choice) && <Check size={15} aria-hidden="true" />}{choice}
                </button>
              ))}
              {question.multiple && <small>Choose any that apply</small>}
            </div>
          )}

          <label className="question-card__detail">
            <span>{question.choices.length ? "Add detail (optional)" : "Your answer"}</span>
            <textarea
              value={detail} onChange={(event) => { setDetail(event.target.value); setError(""); }} onKeyDown={keyDown}
              placeholder={question.placeholder || "A sentence or two is plenty"} rows={3} maxLength={2000} disabled={working}
            />
          </label>

          {(error || interview.notice) && <div className="form-error" role="alert">{error || interview.notice}</div>}

          <div className="question-card__footer">
            <button type="button" className="button button--quiet" onClick={() => void submit(true)} disabled={working}>Skip</button>
            <button className="button button--primary button--large" disabled={working}>
              {working ? "Saving…" : "Next"} {!working && <ArrowRight size={18} />}
            </button>
          </div>
        </form>
      )}

      {added.length > 0 && (
        <section className="just-added" aria-label="Just added to your profile">
          <h2><Check size={16} /> Added to your profile</h2>
          <p>Choose who can see each one, or edit or remove it. "Only me" still helps your matches.</p>
          {added.map((fact) => <FactCard key={`${fact.id}-${fact.updated_at}`} fact={fact} onEdit={editFact} onDelete={deleteFact} />)}
        </section>
      )}

      {learned.length > 0 && (
        <section className="review-all">
          <button type="button" className="button button--quiet" onClick={() => setShowAll((value) => !value)} aria-expanded={showAll}>
            <ChevronDown size={16} className={showAll ? "rotate-180" : ""} /> {showAll ? "Hide" : "Review"} everything we've learned ({learned.length})
          </button>
          {showAll && <FactList facts={learned} onEdit={editFact} onDelete={deleteFact} empty="" />}
        </section>
      )}
    </div>
  );
}
