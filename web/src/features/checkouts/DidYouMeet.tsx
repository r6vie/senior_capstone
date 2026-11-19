import { useState } from "react";
import { api } from "../../api/client";
import { errorMessage } from "../../api/errors";
import type { components } from "../../api/schema";
import { Button } from "../../ui/Button";

type View = components["schemas"]["DidYouMeet"];
type Answer = components["schemas"]["MeetAnswerRequest"]["answer"];

// "Did you meet?" (C4, docs/trove.md §8). Asked after the meeting time; each person answers for themselves
// and nobody is ever shown the other's answer. "Not yet" keeps the checkout open; Yes or No is final and
// returns the copy, so it says so before the press rather than asking again after it.
export function DidYouMeet({
  checkoutId,
  name,
  view,
  returned = false,
  onAnswered,
}: {
  checkoutId: string;
  name: string;
  view: View;
  // The other person's Yes or No already returned the copy: only a final answer is left.
  returned?: boolean;
  onAnswered: (answer: Answer) => void | Promise<void>;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!view.can_answer) return null;

  async function answer(value: Answer) {
    setBusy(true);
    setError(null);
    const { error } = await api.POST("/checkouts/{checkout_id}/met", {
      params: { path: { checkout_id: checkoutId } },
      body: { answer: value },
    });
    if (error) {
      setError(errorMessage(error));
      setBusy(false);
      return;
    }
    await onAnswered(value);
    setBusy(false);
  }

  const notYet = view.my_answer === "not_yet";
  return (
    <fieldset className="meet-question">
      <legend className="caption">Did you meet {name}?</legend>
      <p className="muted">
        {returned
          ? "Only you see your answer."
          : notYet
            ? "You said not yet. Answer again once you've met."
            : "Only you see your answer. Yes or No returns the copy."}
      </p>
      <div className="checkout-actions">
        <Button variant="secondary" disabled={busy} onClick={() => answer("met")}>
          Yes, we met
        </Button>
        {!returned && (
          <Button variant="quiet" disabled={busy} aria-pressed={notYet} onClick={() => answer("not_yet")}>
            Not yet
          </Button>
        )}
        <Button variant="quiet" disabled={busy} onClick={() => answer("no")}>
          No
        </Button>
      </div>
      {error && (
        <p role="alert" className="message message-error">
          <span>!</span>
          <span>{error}</span>
        </p>
      )}
    </fieldset>
  );
}
