import { MapPin } from "lucide-react";
import type { Profile } from "../types";

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

export function ProfileCard({ profile, index }: { profile: Profile; index: number }) {
  return (
    <article className="profile-card">
      <div className="profile-card__heading">
        <div className={`avatar ${avatarColors[index % avatarColors.length]}`}>{initials(profile.name)}</div>
        <div>
          <h3>{profile.name}</h3>
          <p>{profile.affiliation}</p>
        </div>
      </div>
      <p className="profile-card__location"><MapPin size={16} /> {profile.location}</p>
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
    </article>
  );
}
