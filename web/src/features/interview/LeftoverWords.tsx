import { useEffect, useState } from "react";
import { useAuth } from "../auth/AuthProvider";

// Words the member typed that couldn't go where they meant them to: another screen had moved the
// interview on, or a first version was saved and an edit came too late. They stay on every screen,
// selectable, until the member says they're done with them. Nothing a member types just disappears.

const PREFIX = "trove_interview_draft:leftover:";
const CHANGED = "trove-leftover-changed";

interface Leftover {
  message: string;
  text: string;
}

function read(userId: string): Leftover[] {
  try {
    return JSON.parse(localStorage.getItem(PREFIX + userId) ?? "[]") as Leftover[];
  } catch {
    return [];
  }
}

function write(userId: string, items: Leftover[]) {
  try {
    if (items.length) localStorage.setItem(PREFIX + userId, JSON.stringify(items));
    else localStorage.removeItem(PREFIX + userId);
  } catch {
    // Without storage they last as long as the event below does.
  }
  window.dispatchEvent(new Event(CHANGED));
}

export const NOT_SAVED_ANOTHER_SCREEN =
  "Your last words weren't saved, because the questions had already ended on another screen. Here they are:";
export const FIRST_VERSION_SAVED =
  "Your first version was saved. Your changes couldn't be used. Here they are:";
export const STARTED_FOR_EARLIER = "You'd started this for an earlier question. Here it is:";

export function leaveWords(userId: string, message: string, text: string) {
  const items = read(userId);
  if (!items.some((item) => item.text === text)) write(userId, [...items, { message, text }]);
}

function useLeftovers() {
  const { user } = useAuth();
  const userId = user?.id ?? "anon";
  const [items, setItems] = useState(() => read(userId));

  useEffect(() => {
    const update = () => setItems(read(userId));
    update();
    window.addEventListener(CHANGED, update);
    return () => window.removeEventListener(CHANGED, update);
  }, [userId]);

  return { items, userId };
}

/** "Everything you've said is saved" isn't true while words are showing here. */
export function useSavedLine(): string {
  const { items } = useLeftovers();
  return items.length ? "Everything else you've said is saved." : "Everything you've said is saved.";
}

export function LeftoverWords() {
  const { items, userId } = useLeftovers();
  if (!items.length) return null;
  return (
    <div className="iv-leftovers">
      {items.map((item) => (
        <section key={item.text} className="panel iv-leftover" role="status">
          <p>{item.message}</p>
          <blockquote>{item.text}</blockquote>
          <button
            type="button"
            className="button button-quiet iv-sm iv-show"
            onClick={() =>
              write(
                userId,
                read(userId).filter((other) => other.text !== item.text),
              )
            }
          >
            I've got them
          </button>
        </section>
      ))}
    </div>
  );
}
