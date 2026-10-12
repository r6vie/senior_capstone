import { Search, SlidersHorizontal, UsersRound } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ApiError, api } from "../api";
import { useAuth } from "../auth";
import { ProfileCard } from "../components/ProfileCard";
import type { OnboardingStatus, Profile } from "../types";

export function DirectoryPage() {
  const { token, user } = useAuth();
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [query, setQuery] = useState("");
  const [activeQuery, setActiveQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [onboarding, setOnboarding] = useState<OnboardingStatus | null>(null);

  useEffect(() => {
    if (token) api.onboardingStatus(token).then(setOnboarding).catch(() => setOnboarding(null));
  }, [token]);

  useEffect(() => {
    if (!token) return;
    setLoading(true);
    setError("");
    api.profiles(token, activeQuery)
      .then(setProfiles)
      .catch((caught) => setError(caught instanceof ApiError ? caught.message : "Unable to load profiles."))
      .finally(() => setLoading(false));
  }, [token, activeQuery]);

  function search(event: FormEvent) {
    event.preventDefault();
    setActiveQuery(query.trim());
  }

  return (
    <div className="page-wrap">
      <section className="directory-hero">
        <span className="eyebrow eyebrow--blue">CWRU entrepreneurial network</span>
        <h1>Who can help you move forward?</h1>
        <p>Search people by expertise and discover experience across the community.</p>
        <form className="search-box" onSubmit={search}>
          <Search />
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Try “fundraising,” “medical devices,” or “software”…" aria-label="Search expertise" />
          <button className="button button--primary">Search</button>
        </form>
      </section>

      <section className="directory-content">
        <div className="directory-toolbar">
          <div>
            <span className="eyebrow">Network directory</span>
            <h2>{activeQuery ? `Results for “${activeQuery}”` : "People in your circle"}</h2>
          </div>
          <span className="result-count"><UsersRound size={17} /> {profiles.length} {profiles.length === 1 ? "person" : "people"}</span>
        </div>

        {error && <div className="state-card state-card--error">{error}</div>}
        {loading ? (
          <div className="profile-grid" aria-label="Loading profiles">{[0, 1, 2].map((item) => <div className="profile-card profile-card--skeleton" key={item} />)}</div>
        ) : profiles.length ? (
          <div className="profile-grid">{profiles.map((profile, index) => <ProfileCard profile={profile} index={index} key={profile.id} />)}</div>
        ) : (
          <div className="state-card"><SlidersHorizontal /><h3>No matches yet</h3><p>Try a broader expertise term or clear your search.</p><button className="button button--secondary" onClick={() => { setQuery(""); setActiveQuery(""); }}>View everyone</button></div>
        )}

        {onboarding && !onboarding.basics_done ? (
          <aside className="profile-nudge">
            <div><strong>{user?.name?.split(" ")[0]}, tell us what you're looking for.</strong><p>A 30-second form and a short conversation help us find the right people for you.</p></div>
            <Link className="button button--primary" to="/onboarding">Get started</Link>
          </aside>
        ) : onboarding && onboarding.coverage.percent < 75 ? (
          <aside className="profile-nudge">
            <div><strong>Your profile is {onboarding.coverage.percent}% complete.</strong><p>A few more answers help the right people find you.</p></div>
            <Link className="button button--secondary" to="/onboarding/interview">Continue the conversation</Link>
          </aside>
        ) : (
          <aside className="profile-nudge">
            <div><strong>{user?.name?.split(" ")[0]}, is your profile up to date?</strong><p>Clear expertise and interests help the right people find you.</p></div>
            <Link className="button button--secondary" to="/app/profile">Review my profile</Link>
          </aside>
        )}
      </section>
    </div>
  );
}
