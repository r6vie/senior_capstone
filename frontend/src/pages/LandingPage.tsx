import { ArrowRight, MessageSquareText, Search, Sparkles, UsersRound } from "lucide-react";
import { Link } from "react-router-dom";
import { useAuth } from "../auth";
import { Brand } from "../components/Brand";

export function LandingPage() {
  const { token } = useAuth();

  return (
    <div className="landing">
      <header className="landing-nav">
        <Brand />
        <nav aria-label="Main navigation">
          <a href="#how-it-works">How it works</a>
          <a href="#community">Community</a>
          {token ? (
            <Link className="button button--primary" to="/app">Open network <ArrowRight size={17} /></Link>
          ) : (
            <>
              <Link className="nav-login" to="/login">Log in</Link>
              <Link className="button button--primary" to="/signup">Join FoundersCircle <ArrowRight size={17} /></Link>
            </>
          )}
        </nav>
      </header>

      <main>
        <section className="hero">
          <div className="hero__copy">
            <div className="hero__badge"><Sparkles size={15} /> Built for the CWRU entrepreneurial community</div>
            <h1>The right connection can change everything.</h1>
            <p>
              Find founders, mentors, and alumni whose experience matches what you are building—and what you need next.
            </p>
            <div className="hero__actions">
              <Link className="button button--primary button--large" to={token ? "/app" : "/signup"}>
                Explore the network <ArrowRight size={19} />
              </Link>
              <a className="button button--secondary button--large" href="#how-it-works">See how it works</a>
            </div>
            <div className="hero__trust">
              <div className="avatar-stack" aria-hidden="true">
                <span>AM</span><span>JR</span><span>TL</span><span>+</span>
              </div>
              <p><strong>One connected ecosystem</strong><br />Students, alumni, mentors, and founders</p>
            </div>
          </div>

          <div className="network-visual" aria-label="Illustration of connected community members">
            <div className="network-visual__glow" />
            <div className="network-line network-line--one" />
            <div className="network-line network-line--two" />
            <div className="network-line network-line--three" />
            <div className="network-person network-person--center">
              <span className="avatar avatar--navy">YC</span>
              <strong>Your next connection</strong>
              <small>Starts with a need</small>
            </div>
            <div className="network-person network-person--one">
              <span className="avatar avatar--blue">MR</span>
              <strong>Maya R.</strong><small>Healthcare founder</small>
            </div>
            <div className="network-person network-person--two">
              <span className="avatar avatar--teal">DK</span>
              <strong>Daniel K.</strong><small>Growth mentor</small>
            </div>
            <div className="network-person network-person--three">
              <span className="avatar avatar--gold">SL</span>
              <strong>Sam L.</strong><small>Alumni investor</small>
            </div>
          </div>
        </section>

        <section className="steps" id="how-it-works">
          <div className="section-heading">
            <span className="eyebrow eyebrow--blue">How it works</span>
            <h2>Make the network useful, not overwhelming.</h2>
          </div>
          <div className="steps__grid">
            <article><span className="step-icon"><UsersRound /></span><span className="step-number">01</span><h3>Tell us who you are</h3><p>Build a profile around your background, interests, and areas of expertise.</p></article>
            <article><span className="step-icon"><Search /></span><span className="step-number">02</span><h3>Search with intent</h3><p>Look for the exact knowledge and experience your next challenge requires.</p></article>
            <article><span className="step-icon"><MessageSquareText /></span><span className="step-number">03</span><h3>Start a meaningful conversation</h3><p>Understand the fit, then reach out with shared context from the beginning.</p></article>
          </div>
        </section>

        <section className="community-banner" id="community">
          <div><span className="eyebrow">The FoundersCircle vision</span><h2>Where ambition meets experience.</h2></div>
          <p>A living map of the people, knowledge, and momentum inside the CWRU entrepreneurship ecosystem.</p>
          <Link className="button button--light" to={token ? "/app" : "/signup"}>Find your people <ArrowRight size={17} /></Link>
        </section>
      </main>

      <footer className="landing-footer"><Brand light /><p>Built for the CWRU entrepreneurial community.</p></footer>
    </div>
  );
}
