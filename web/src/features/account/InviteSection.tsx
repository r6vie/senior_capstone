import { useEffect, useState } from "react";
import { api } from "../../api/client";
import { errorMessage } from "../../api/errors";
import type { components } from "../../api/schema";
import { Button } from "../../ui/Button";

type Invite = components["schemas"]["InviteView"];

// Alumni join through a member (docs/trove.md §9.2): each link works once, lasts 14 days, and a member
// can have 5 open. The link is shown only when it is made; the API keeps just a hash of it.
export function InviteSection() {
  const [open, setOpen] = useState<Invite[]>([]);
  const [link, setLink] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let stale = false;
    api.GET("/auth/invites").then(({ data }) => {
      if (!stale && Array.isArray(data)) setOpen(data);
    });
    return () => {
      stale = true;
    };
  }, []);

  async function make() {
    setBusy(true);
    setError(null);
    setCopied(false);
    const { data, error: problem } = await api.POST("/auth/invites");
    setBusy(false);
    if (!data) return setError(errorMessage(problem));
    setLink(data.link);
    setOpen((current) => [
      { id: data.id, created_at: data.created_at, expires_at: data.expires_at },
      ...current,
    ]);
  }

  async function cancel(id: string) {
    setError(null);
    const { response, error: problem } = await api.DELETE("/auth/invites/{invite_id}", {
      params: { path: { invite_id: id } },
    });
    if (!response.ok) return setError(errorMessage(problem));
    setOpen((current) => current.filter((invite) => invite.id !== id));
  }

  async function copy() {
    if (!link) return;
    try {
      await navigator.clipboard.writeText(link);
      setCopied(true);
    } catch {
      setCopied(false);
    }
  }

  return (
    <section aria-labelledby="invite-heading" className="settings-section">
      <h2 id="invite-heading" className="settings-heading">
        Invite an alum
      </h2>
      <p className="muted">
        Alumni join with a link from a member. Each link works once and lasts 14 days. You can have 5 open at
        a time.
      </p>
      {link && (
        <div className="stack" role="status">
          <label className="field">
            <span>Your new link (shown only now)</span>
            <input readOnly value={link} onFocus={(event) => event.currentTarget.select()} />
          </label>
          <div>
            <Button variant="secondary" onClick={copy}>
              {copied ? "Copied" : "Copy link"}
            </Button>
          </div>
        </div>
      )}
      {error && (
        <p role="alert" className="message message-error settings-error">
          <span>!</span>
          <span>{error}</span>
        </p>
      )}
      <div>
        <Button variant="secondary" onClick={make} disabled={busy} aria-busy={busy}>
          Make an invite link
        </Button>
      </div>
      {open.length > 0 && (
        <ul className="settings-invites">
          {open.map((invite) => (
            <li key={invite.id}>
              <span>
                Open until{" "}
                {new Date(invite.expires_at).toLocaleDateString(undefined, { month: "long", day: "numeric" })}
              </span>
              <Button variant="quiet" onClick={() => cancel(invite.id)}>
                Cancel
              </Button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
