import { type FormEvent, useEffect, useState } from "react";
import { api } from "../../api/client";
import { errorMessage } from "../../api/errors";
import { Button } from "../../ui/Button";
import { PageLoading } from "../../ui/Loading";
import { TextField } from "../../ui/TextField";
import { useAuth } from "../auth/AuthProvider";
import { InviteSection } from "./InviteSection";
import { type Affiliation, MemberContextFields } from "./MemberContextFields";
import "./SettingsPage.css";
import { usePageTitle } from "../../ui/usePageTitle";

// Account settings (plan item A1): what to share when an author says yes, the one email switch, and
// deleting the account. Contact details never appear on a book (docs/trove.md §9.1).

type Notice = { kind: "saved" | "error"; text: string } | null;

function Feedback({ notice }: { notice: Notice }) {
  if (!notice) return null;
  return (
    <p role={notice.kind === "error" ? "alert" : "status"} className={`message settings-${notice.kind}`}>
      <span>{notice.kind === "error" ? "!" : "✓"}</span>
      <span>{notice.text}</span>
    </p>
  );
}

function ContactSection({ email }: { email: string }) {
  const [linkedin, setLinkedin] = useState("");
  const [phone, setPhone] = useState("");
  const [loaded, setLoaded] = useState(false);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<Notice>(null);

  useEffect(() => {
    // A response from an earlier request must not overwrite what the member has since typed.
    let stale = false;
    api.GET("/auth/me/contact").then(({ data }) => {
      if (stale) return;
      if (data) {
        setLinkedin(data.linkedin_url ?? "");
        setPhone(data.phone ?? "");
        setLoaded(true);
      } else {
        setNotice({ kind: "error", text: "We couldn't load your contact details. Please refresh." });
      }
    });
    return () => {
      stale = true;
    };
  }, []);

  async function save(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setNotice(null);
    const { data, error } = await api.PUT("/auth/me/contact", {
      body: { linkedin_url: linkedin.trim() || null, phone: phone.trim() || null },
    });
    setBusy(false);
    if (!data) return setNotice({ kind: "error", text: errorMessage(error) });
    setLinkedin(data.linkedin_url ?? "");
    setPhone(data.phone ?? "");
    setNotice({ kind: "saved", text: "Contact details saved." });
  }

  return (
    <section aria-labelledby="contact-heading" className="page-row">
      {/* Settings appears once the contact details are in, so the fields don't fill in under the cursor. */}
      {!loaded && !notice && <PageLoading />}
      <div className="page-row-head">
        <h2 id="contact-heading">Contact details</h2>
        <p>
          Shared only with someone whose checkout you accept, or the author who accepts yours. Never on your
          book.
        </p>
      </div>
      <form onSubmit={save} className="page-row-body">
        <p className="settings-fixed">
          <span className="caption">Always shared</span> {email}
        </p>
        <div className="settings-pair">
          <TextField
            label="LinkedIn profile (optional)"
            value={linkedin}
            onChange={setLinkedin}
            autoComplete="url"
          />
          <TextField label="Phone (optional)" value={phone} onChange={setPhone} autoComplete="tel" />
        </div>
        <Feedback notice={notice} />
        <div>
          <Button type="submit" disabled={busy || !loaded} aria-busy={busy}>
            Save contact details
          </Button>
        </div>
      </form>
    </section>
  );
}

function EmailSection({ initial, onChanged }: { initial: boolean; onChanged: () => void }) {
  const [enabled, setEnabled] = useState(initial);
  const [notice, setNotice] = useState<Notice>(null);

  async function change(next: boolean) {
    setNotice(null);
    const { data, error } = await api.PUT("/auth/me/notifications", { body: { email_notifications: next } });
    if (!data) return setNotice({ kind: "error", text: errorMessage(error) });
    setEnabled(data.email_notifications);
    onChanged();
    setNotice({
      kind: "saved",
      text: data.email_notifications ? "Email notifications are on." : "Email notifications are off.",
    });
  }

  return (
    <section aria-labelledby="email-heading" className="page-row">
      <div className="page-row-head">
        <h2 id="email-heading">Email</h2>
        <p>Account emails, like your welcome message, are sent either way.</p>
      </div>
      <div className="page-row-body page-row-bare">
        <label className="choice">
          <input type="checkbox" checked={enabled} onChange={(event) => change(event.target.checked)} />
          <span>Email me about checkouts and messages</span>
        </label>
        <Feedback notice={notice} />
      </div>
    </section>
  );
}

function MemberContextSection({
  initialAffiliations,
  initialFounder,
  onChanged,
}: {
  initialAffiliations: Affiliation[];
  initialFounder: boolean;
  onChanged: () => Promise<void>;
}) {
  const [affiliations, setAffiliations] = useState(initialAffiliations);
  const [founder, setFounder] = useState(initialFounder);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<Notice>(null);

  async function save(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setNotice(null);
    const { data, error } = await api.PUT("/auth/me/context", { body: { affiliations, founder } });
    setBusy(false);
    if (!data) return setNotice({ kind: "error", text: errorMessage(error) });
    setAffiliations(data.affiliations ?? []);
    setFounder(data.founder ?? false);
    await Promise.resolve(onChanged()).catch(() => undefined);
    setNotice({ kind: "saved", text: "Community context saved." });
  }

  return (
    <section aria-labelledby="context-heading" className="settings-section">
      <h2 id="context-heading" className="settings-heading">
        About you
      </h2>
      <form onSubmit={save} className="stack">
        <MemberContextFields
          affiliations={affiliations}
          founder={founder}
          onAffiliationsChange={setAffiliations}
          onFounderChange={setFounder}
        />
        <Feedback notice={notice} />
        <div>
          <Button
            type="submit"
            variant="secondary"
            disabled={busy || affiliations.length === 0}
            aria-busy={busy}
          >
            Save community context
          </Button>
        </div>
      </form>
    </section>
  );
}

function DeleteSection({ email }: { email: string }) {
  const { signOut } = useAuth();
  const [typed, setTyped] = useState("");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<Notice>(null);

  async function remove(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setNotice(null);
    const { response, error } = await api.DELETE("/auth/me", { body: { email: typed.trim() } });
    if (!response.ok) {
      setBusy(false);
      return setNotice({ kind: "error", text: errorMessage(error) });
    }
    await signOut();
  }

  return (
    <section aria-labelledby="delete-heading" className="page-row">
      <div className="page-row-head">
        <h2 id="delete-heading">Delete your account</h2>
        <p>
          This removes your account, your book, and your checkouts and meetings, for the other person too. It
          can't be undone. To confirm, type your email address: <strong>{email}</strong>
        </p>
      </div>
      <form onSubmit={remove} className="page-row-body">
        <TextField
          label="Your email address"
          type="email"
          value={typed}
          onChange={setTyped}
          autoComplete="off"
        />
        <Feedback notice={notice} />
        <div>
          <Button
            type="submit"
            variant="secondary"
            disabled={busy || typed.trim().toLowerCase() !== email.toLowerCase()}
            aria-busy={busy}
          >
            Delete my account
          </Button>
        </div>
      </form>
    </section>
  );
}

export function SettingsPage() {
  usePageTitle("Settings");
  const { user, refreshUser } = useAuth();
  if (!user) return null;

  return (
    <main className="shell-page page-wide settings-page">
      <h1 className="page-title">Settings</h1>
      <MemberContextSection
        initialAffiliations={user.affiliations ?? []}
        initialFounder={user.founder ?? false}
        onChanged={refreshUser}
      />
      <ContactSection email={user.email} />
      <EmailSection initial={user.email_notifications} onChanged={refreshUser} />
      <InviteSection />
      <DeleteSection email={user.email} />
    </main>
  );
}
