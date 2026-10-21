import { FileText, MessageCircle, SlidersHorizontal } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ApiError, api } from "../api";
import { useAuth } from "../auth";
import type { Fact, FactEdit, OnboardingStatus } from "../types";
import { CoverageMeter, FactList } from "./Facts";

/** Everything the network knows about you, editable, plus the exact text matching reads. */
export function MyData() {
  const { token } = useAuth();
  const [status, setStatus] = useState<OnboardingStatus | null>(null);
  const [facts, setFacts] = useState<Fact[]>([]);
  const [markdown, setMarkdown] = useState<string | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) return;
    Promise.all([api.onboardingStatus(token), api.myFacts(token)])
      .then(([loadedStatus, loadedFacts]) => { setStatus(loadedStatus); setFacts(loadedFacts); })
      .catch((caught) => setError(caught instanceof ApiError ? caught.message : "Unable to load your data."));
  }, [token]);

  async function refresh() {
    if (!token) return;
    setStatus(await api.onboardingStatus(token));
    if (markdown !== null) setMarkdown(await api.myProfileMarkdown(token));
  }

  async function editFact(fact: Fact, edit: FactEdit) {
    if (!token) return;
    try {
      const updated = await api.editFact(token, fact.id, edit);
      setFacts((current) => current.map((item) => (item.id === fact.id ? updated : item)));
      await refresh();
    } catch (caught) { setError(caught instanceof ApiError ? caught.message : "Unable to update that fact."); }
  }

  async function deleteFact(fact: Fact) {
    if (!token) return;
    try {
      await api.deleteFact(token, fact.id);
      setFacts((current) => current.filter((item) => item.id !== fact.id));
      await refresh();
    } catch (caught) { setError(caught instanceof ApiError ? caught.message : "Unable to delete that fact."); }
  }

  async function toggleMarkdown() {
    if (!token) return;
    if (markdown !== null) { setMarkdown(null); return; }
    try { setMarkdown(await api.myProfileMarkdown(token)); }
    catch (caught) { setError(caught instanceof ApiError ? caught.message : "Unable to load your profile text."); }
  }

  if (error) return <div className="form-error" role="alert">{error}</div>;
  if (!status) return null;

  if (!status.basics_done) {
    return (
      <section className="form-section my-data my-data--empty">
        <div><h2>Tell us what you're looking for</h2><p>A 30-second form and a short conversation help us find the right people for you.</p></div>
        <Link className="button button--primary" to="/onboarding">Get started</Link>
      </section>
    );
  }

  return (
    <section className="form-section my-data">
      <div className="my-data__top">
        <div>
          <h2>What the network knows about you</h2>
          <p>Everything here came from your basics and your conversation. You decide who sees each item.</p>
        </div>
        <div className="my-data__actions">
          <Link className="button button--primary" to="/onboarding/interview"><MessageCircle size={16} /> Continue conversation</Link>
          <Link className="button button--secondary" to="/onboarding"><SlidersHorizontal size={16} /> Edit basics</Link>
        </div>
      </div>
      <CoverageMeter coverage={status.coverage} />
      <FactList facts={facts} onEdit={editFact} onDelete={deleteFact} empty="Nothing yet. Start the conversation to add to your profile." />
      <button type="button" className="button button--quiet my-data__markdown-toggle" onClick={toggleMarkdown}>
        <FileText size={16} /> {markdown === null ? "Show exactly what matching reads" : "Hide profile text"}
      </button>
      {markdown !== null && <pre className="my-data__markdown">{markdown}</pre>}
    </section>
  );
}
