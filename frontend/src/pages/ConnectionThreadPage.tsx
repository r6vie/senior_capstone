import { ArrowLeft, Send } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ApiError, api } from "../api";
import { useAuth } from "../auth";
import type { ThreadMessage } from "../types";

export function ConnectionThreadPage() {
  const { id = "" } = useParams();
  const { token } = useAuth();
  const [thread, setThread] = useState<ThreadMessage[]>([]);
  const [body, setBody] = useState("");
  const [error, setError] = useState("");
  const [sending, setSending] = useState(false);

  useEffect(() => {
    if (!token) return;
    api.messages(token, id)
      .then(setThread)
      .catch((caught) => setError(caught instanceof ApiError ? caught.message : "Unable to load the conversation."));
  }, [token, id]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!token) return;
    setSending(true); setError("");
    try {
      const message = await api.sendMessage(token, id, body.trim());
      setThread((current) => [...current, message]);
      setBody("");
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Unable to send your message.");
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="page-wrap">
      <Link className="back-link" to="/app/connections"><ArrowLeft /> Back to requests</Link>
      <div className="thread">
        {thread.map((message) => (
          <div key={message.id} className={`bubble ${message.from_me ? "bubble--me" : "bubble--them"}`}>
            <p>{message.body}</p>
            <small>{new Date(message.created_at).toLocaleString()}</small>
          </div>
        ))}
      </div>
      <form className="profile-form" onSubmit={submit}>
        {error && <div className="form-error" role="alert">{error}</div>}
        <textarea value={body} onChange={(event) => setBody(event.target.value)} maxLength={1000} rows={3} required placeholder="Write a reply…" />
        <button className="button button--primary" disabled={sending || !body.trim()}><Send /> {sending ? "Sending…" : "Send"}</button>
      </form>
    </div>
  );
}
