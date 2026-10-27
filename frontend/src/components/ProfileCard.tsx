import { BookOpenText, MapPin, MessageSquareText, MessagesSquare, X } from "lucide-react";
import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import { Link } from "react-router-dom";
import type { Connection, Profile } from "../types";

const avatarColors = ["avatar--navy", "avatar--blue", "avatar--teal", "avatar--gold"];

function initials(name: string) {
  return name
    .replace(/\s*\(fictional\)\s*/i, "")
    .split(/\s+/)
    .slice(0, 2)
    .map((word) => word[0])
    .join("")
    .toUpperCase();
}

export function ProfileCard({
  profile, index, onConnect, connection,
}: { profile: Profile; index: number; onConnect?: (profile: Profile) => void; connection?: Connection }) {
  const [expanded, setExpanded] = useState(false);
  const cardRef = useRef<HTMLElement>(null);
  const canExpand = Boolean(onConnect);

  // While open: a click outside the card (or Escape) closes it.
  useEffect(() => {
    if (!expanded) return;
    const onPointerDown = (event: MouseEvent) => {
      if (cardRef.current && !cardRef.current.contains(event.target as Node)) setExpanded(false);
    };
    const onKey = (event: globalThis.KeyboardEvent) => { if (event.key === "Escape") setExpanded(false); };
    document.addEventListener("mousedown", onPointerDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onPointerDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [expanded]);

  // Bring the larger card fully into view after it opens.
  useEffect(() => {
    if (expanded) cardRef.current?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }, [expanded]);

  function open() {
    if (canExpand && !expanded) setExpanded(true);
  }

  function keyDown(event: KeyboardEvent<HTMLElement>) {
    if (event.target === event.currentTarget && (event.key === "Enter" || event.key === " ")) {
      event.preventDefault();
      open();
    }
  }

  return (
    <article
      ref={cardRef}
      className={`profile-card ${canExpand ? "profile-card--clickable" : ""} ${expanded ? "profile-card--expanded" : ""}`}
      onClick={open}
      onKeyDown={canExpand ? keyDown : undefined}
      tabIndex={canExpand && !expanded ? 0 : undefined}
    >
      {expanded && (
        <button type="button" className="profile-card__close" onClick={() => setExpanded(false)} aria-label="Close profile">
          <X size={18} />
        </button>
      )}
      <div className="profile-card__heading">
        <div className={`avatar ${avatarColors[index % avatarColors.length]}`}>{initials(profile.name)}</div>
        <div>
          <h3>{profile.name}</h3>
          <p>{profile.affiliation}</p>
        </div>
      </div>
      <p className="profile-card__location"><MapPin size={16} /> {profile.location}</p>

      {expanded ? (
        <>
          <div className="profile-card__columns">
            <div className="profile-card__section">
              <span className="eyebrow">Expertise</span>
              <div className="tags">
                {profile.expertise.length
                  ? profile.expertise.map((item) => <span className="tag" key={item}>{item}</span>)
                  : <span className="profile-card__empty">Not listed yet</span>}
              </div>
            </div>
            <div className="profile-card__section">
              <span className="eyebrow">Interested in</span>
              <div className="tags">
                {profile.interests.length
                  ? profile.interests.map((item) => <span className="tag tag--interest" key={item}>{item}</span>)
                  : <span className="profile-card__empty">Open to new ideas</span>}
              </div>
            </div>
          </div>
          <div className="profile-card__actions">
            {profile.role === "alumni" && (
              <Link className="button button--secondary" to={`/app/prepare/${profile.id}`} onClick={(event) => event.stopPropagation()}>
                <BookOpenText size={17} /> Meeting prep
              </Link>
            )}
            {connection ? (
              <div className="profile-card__existing">
                <span className={`status status--${connection.status}`}>
                  {connection.direction === "outgoing" ? "You messaged them" : "They messaged you"} · {connection.status}
                </span>
                <Link className="button button--primary" to={`/app/connections/${connection.id}`}>
                  <MessagesSquare size={17} /> View message history
                </Link>
              </div>
            ) : (
              <button type="button" className="button button--primary" onClick={() => onConnect?.(profile)}>
                <MessageSquareText size={17} /> Connect with {profile.name.split(" ")[0]}
              </button>
            )}
          </div>
        </>
      ) : (
        <>
          <div className="profile-card__section">
            <span className="eyebrow">Expertise</span>
            <div className="tags">
              {profile.expertise.map((item) => <span className="tag" key={item}>{item}</span>)}
            </div>
          </div>
          <div className="profile-card__section">
            <span className="eyebrow">Interested in</span>
            <p className="profile-card__interests">{profile.interests.join(" · ") || "Open to new ideas"}</p>
          </div>
        </>
      )}
    </article>
  );
}
