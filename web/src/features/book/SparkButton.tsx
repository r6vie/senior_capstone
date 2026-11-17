import { useState } from "react";
import { api } from "../../api/client";
import "./SparkButton.css";

// "I have one like this" (trove.md §3, board G4): a private note to self on a chapter of someone else's
// book. It saves the chapter's title for the member's own next questions, and the other author never
// sees any trace of it. For the reader's book page (D1) to mount at the end of a chapter's content.
//
// Mounting: never on the member's own book. Fetch GET /interview/sparks once for the page and pass each
// chapter's spark id as `sparkId`, so the saved state survives a reload.

type Status = "rest" | "saving" | "saved" | "limit" | "failed";

export function SparkButton({
  bookId,
  chapterId,
  chapterTitle,
  sparkId,
  hasBook = true,
}: {
  bookId: string;
  chapterId: string;
  chapterTitle: string;
  /** The member's saved spark for this chapter, if there is one. */
  sparkId?: string;
  /** Whether the member has a book yet, which changes which interview this is for. */
  hasBook?: boolean;
}) {
  const [saved, setSaved] = useState(sparkId);
  const [status, setStatus] = useState<Status>(sparkId ? "saved" : "rest");
  const forWhat = hasBook ? "your next interview" : "your interview";

  async function save() {
    setStatus("saving");
    try {
      const { data, response } = await api.POST("/interview/sparks", {
        body: { book_id: bookId, chapter_id: chapterId },
      });
      if (data) {
        setSaved(data.id);
        setStatus("saved");
      } else {
        setStatus(response.status === 409 ? "limit" : "failed");
      }
    } catch {
      setStatus("failed");
    }
  }

  async function undo() {
    setStatus("rest");
    try {
      const { response } = await api.DELETE("/interview/sparks/{spark_id}", {
        params: { path: { spark_id: saved ?? "" } },
      });
      if (!response.ok) setStatus("saved");
      else setSaved(undefined);
    } catch {
      setStatus("saved");
    }
  }

  if (status === "saved") {
    return (
      <span className="spk" role="status">
        <span className="spk-said">Saved for {forWhat}</span>
        <button type="button" className="spk-link" aria-label={`Undo saving ${chapterTitle}`} onClick={undo}>
          Undo
        </button>
      </span>
    );
  }
  if (status === "limit") {
    return (
      <span className="spk spk-said" role="status">
        You've saved as many as I can hold. Remove one from My book to save this.
      </span>
    );
  }
  if (status === "failed") {
    return (
      <span className="spk" role="status">
        <span className="spk-said">Couldn't save that.</span>
        <button
          type="button"
          className="spk-link"
          aria-label={`Try saving ${chapterTitle} again`}
          onClick={save}
        >
          Try again
        </button>
      </span>
    );
  }
  return (
    <span className="spk">
      <button
        type="button"
        className="spk-link spk-main"
        aria-label={`I have one like this: ${chapterTitle}`}
        aria-busy={status === "saving"}
        disabled={status === "saving"}
        onClick={save}
      >
        I have one like this
      </button>
      <span className="spk-tip" role="tooltip">
        Saves this chapter's title for {hasBook ? "your own next interview" : "your interview"}. Nothing else
        is copied.
      </span>
    </span>
  );
}
