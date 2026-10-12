import { Check, MessageSquareText, X } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ApiError, api } from "../api";
import { useAuth } from "../auth";
import type { Connection } from "../types";

const typeLabel = (type: string) => type.replace("_", " ");

export function ConnectionsPage() {
  const { token } = useAuth();
  const [items, setItems] = useState<Connection[]>([]);
  const [tab, setTab] = useState<"incoming" | "outgoing">("incoming");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) return;
    api.connections(token)
      .then(setItems)
      .catch((caught) => setError(caught instanceof ApiError ? caught.message : "Unable to load requests."))
      .finally(() => setLoading(false));
  }, [token]);

  async function respond(item: Connection, status: "accepted" | "declined") {
    if (!token) return;
    const id = item.id;
    if (status === "accepted" && !window.confirm(
      `Accepting shares your email address with ${item.profile?.name ?? "this member"}, and theirs with you. Continue?`,
    )) return;
    setError("");
    try {
      const updated = await api.respond(token, id, status);
      setItems((current) => current.map((item) => (item.id === id ? updated : item)));
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Unable to respond.");
    }
  }

  const shown = items.filter((item) => item.direction === tab);

  return (
    <div className="page-wrap">
      <span className="eyebrow eyebrow--blue">Your conversations</span>
      <h1>Requests</h1>
      <div className="tabs" role="tablist">
        <button role="tab" aria-selected={tab === "incoming"} className={tab === "incoming" ? "tab tab--active" : "tab"} onClick={() => setTab("incoming")}>Received</button>
        <button role="tab" aria-selected={tab === "outgoing"} className={tab === "outgoing" ? "tab tab--active" : "tab"} onClick={() => setTab("outgoing")}>Sent</button>
      </div>

      {error && <div className="state-card state-card--error">{error}</div>}
      {loading ? (
        <div className="loading-panel"><span className="spinner" />Loading…</div>
      ) : shown.length === 0 ? (
        <div className="state-card">
          <MessageSquareText />
          <h3>Nothing here yet</h3>
          <p>{tab === "incoming" ? "Requests people send you will appear here." : "Find someone in the directory and press Connect."}</p>
        </div>
      ) : (
        shown.map((item) => (
          <article className="request-card" key={item.id}>
            <div className="request-card__top">
              <strong>{item.profile?.name ?? "Member"}</strong>
              <span className="tag">{typeLabel(item.type)}</span>
              <span className={`status status--${item.status}`}>{item.status}</span>
            </div>
            {item.profile && <small>{item.profile.affiliation} · {item.profile.location}</small>}
            <p>{item.message}</p>
            {item.contact_email && <p>Email: <a href={`mailto:${item.contact_email}`}>{item.contact_email}</a></p>}
            <div className="request-card__actions">
              {item.direction === "incoming" && item.status === "pending" && (
                <>
                  <button className="button button--primary" onClick={() => respond(item, "accepted")}><Check /> Accept</button>
                  <button className="button button--secondary" onClick={() => respond(item, "declined")}><X /> Decline</button>
                </>
              )}
              {item.direction === "incoming" && item.status === "pending" && (
                <small className="request-card__note">Accepting shares your email with {item.profile?.name ?? "them"}, and theirs with you.</small>
              )}
              {item.status !== "declined" && (
                <Link className="button button--secondary" to={`/app/connections/${item.id}`}>Open conversation</Link>
              )}
            </div>
          </article>
        ))
      )}
    </div>
  );
}
