import { ArrowRight, BookOpenText, BriefcaseBusiness, MapPin, Search, Sparkles, UserRoundCheck } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ApiError, api } from "../api";
import { useAuth } from "../auth";
import type { MatchResult, ProfileInput } from "../types";

const breakdownLabels: Record<string, string> = {
  expertise: "Expertise",
  interests: "Shared interests",
  help_alignment: "Help alignment",
  background: "Background",
  availability: "Availability",
  location: "Location",
};

function MatchCard({ match }: { match: MatchResult }) {
  const { profile } = match;
  return (
    <article className="match-card">
      <div className="match-card__top">
        <div className="match-score" style={{ "--score": `${match.score * 3.6}deg` } as React.CSSProperties}>
          <strong>{match.score}%</strong><span>match</span>
        </div>
        <div className="match-card__identity">
          <span className="eyebrow">CWRU alumni</span>
          <h3>{profile.name}</h3>
          <p>{profile.affiliation}</p>
        </div>
      </div>
      <div className="match-card__meta">
        <span><BriefcaseBusiness /> {profile.industry || "Industry not specified"}</span>
        <span><MapPin /> {profile.location}</span>
      </div>
      {profile.background && <p className="match-card__background">{profile.background}</p>}
      <div className="match-reasons">
        <span className="eyebrow eyebrow--blue">Why this match</span>
        <ul>{match.reasons.map((reason) => <li key={reason}><Sparkles /> {reason}</li>)}</ul>
      </div>
      <details className="score-details">
        <summary>See score breakdown</summary>
        <div>{Object.entries(match.score_breakdown).map(([key, value]) => <p key={key}><span>{breakdownLabels[key] ?? key}</span><strong>{value}</strong></p>)}</div>
      </details>
      <Link className="button button--primary match-card__prepare" to={`/app/prepare/${profile.id}`}>
        <BookOpenText size={17} /> Prepare for a meeting
      </Link>
    </article>
  );
}

export function MatchPage() {
  const { token, user } = useAuth();
  const [query, setQuery] = useState("");
  const [industry, setIndustry] = useState("");
  const [location, setLocation] = useState("");
  const [meetingPreference, setMeetingPreference] = useState<"" | ProfileInput["meeting_preference"]>("");
  const [recommendations, setRecommendations] = useState<MatchResult[]>([]);
  const [results, setResults] = useState<MatchResult[] | null>(null);
  const [loadingRecommendations, setLoadingRecommendations] = useState(true);
  const [searching, setSearching] = useState(false);
  const [needsProfile, setNeedsProfile] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) return;
    api.recommendedMatches(token)
      .then(setRecommendations)
      .catch((caught) => {
        if (caught instanceof ApiError && caught.status === 409) setNeedsProfile(true);
        else setError(caught instanceof ApiError ? caught.message : "Unable to load recommendations.");
      })
      .finally(() => setLoadingRecommendations(false));
  }, [token]);

  async function search(event: FormEvent) {
    event.preventDefault();
    if (!token) return;
    setSearching(true); setError(""); setNeedsProfile(false);
    try {
      const matches = await api.searchMatches(token, {
        query,
        industry,
        location,
        meeting_preference: meetingPreference || undefined,
      });
      setResults(matches);
    } catch (caught) {
      if (caught instanceof ApiError && caught.status === 409) setNeedsProfile(true);
      else setError(caught instanceof ApiError ? caught.message : "Unable to find matches.");
    } finally {
      setSearching(false);
    }
  }

  return (
    <div className="page-wrap matches-page">
      <section className="match-hero">
        <div className="match-hero__copy">
          <span className="eyebrow">Personalized alumni matching</span>
          <h1>Find someone who can help you move forward.</h1>
          <p>Tell us what you are working through. We will combine that need with your profile and explain every match.</p>
        </div>
        <form className="match-search" onSubmit={search}>
          <label htmlFor="match-query">What do you need help with?</label>
          <div className="match-search__query"><Search /><textarea id="match-query" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="I need advice from someone who has raised funding for a healthcare startup…" rows={3} minLength={3} maxLength={500} required /></div>
          <div className="match-filters">
            <label>Industry<input value={industry} onChange={(event) => setIndustry(event.target.value)} placeholder="Healthcare" /></label>
            <label>Preferred location<input value={location} onChange={(event) => setLocation(event.target.value)} placeholder="Cleveland, Ohio" /></label>
            <label>Meeting style<select value={meetingPreference} onChange={(event) => setMeetingPreference(event.target.value as typeof meetingPreference)}><option value="">No preference</option><option value="either">Either</option><option value="remote">Remote</option><option value="in_person">In person</option></select></label>
          </div>
          <button className="button button--light button--large" disabled={searching}>{searching ? "Finding matches…" : "Find my matches"}<ArrowRight /></button>
        </form>
      </section>

      {needsProfile && <section className="profile-gate"><UserRoundCheck /><div><h2>Complete your profile first</h2><p>Your interests, goals, and location give the algorithm the context it needs to make useful recommendations.</p></div><Link className="button button--primary" to="/app/profile">Complete profile</Link></section>}
      {error && <div className="state-card state-card--error" role="alert">{error}</div>}

      {results !== null && !needsProfile && (
        <section className="match-section">
          <div className="match-section__heading"><div><span className="eyebrow eyebrow--blue">Based on your current need</span><h2>Your strongest matches</h2></div><span className="result-count">{results.length} {results.length === 1 ? "match" : "matches"}</span></div>
          {results.length ? <div className="match-grid">{results.map((match) => <MatchCard match={match} key={match.profile.id} />)}</div> : <div className="state-card"><Search /><h3>No alumni matched those filters</h3><p>Try removing a filter or describing the need more broadly.</p></div>}
        </section>
      )}

      {!needsProfile && (
        <section className="match-section match-section--recommended">
          <div className="match-section__heading"><div><span className="eyebrow eyebrow--blue">Always working in the background</span><h2>Recommended for {user?.name?.split(" ")[0] ?? "you"}</h2><p>These suggestions use the interests, needs, and industry saved in your profile.</p></div><Sparkles className="match-section__sparkle" /></div>
          {loadingRecommendations ? <div className="match-grid" aria-label="Loading recommendations">{[0, 1, 2].map((item) => <div className="match-card match-card--skeleton" key={item} />)}</div> : recommendations.length ? <div className="match-grid">{recommendations.map((match) => <MatchCard match={match} key={match.profile.id} />)}</div> : <div className="state-card"><UserRoundCheck /><h3>Recommendations are taking shape</h3><p>As alumni complete matching-ready profiles, their recommendations will appear here.</p></div>}
        </section>
      )}
    </div>
  );
}
