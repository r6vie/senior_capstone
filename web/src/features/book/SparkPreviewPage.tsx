import { SparkButton } from "./SparkButton";

// Dev only: lets SparkButton be seen before the reader's book page (D1) mounts it. Registered in App.tsx
// behind import.meta.env.DEV, so it's never in a production build. The ids aren't real, so pressing it
// shows the failed state unless they match a real chapter.

export function SparkPreviewPage() {
  return (
    <main className="narrow-page">
      <h1>SparkButton preview</h1>
      <p>Rest</p>
      <SparkButton bookId="preview" chapterId="rest" chapterTitle="How I decided between two offers" />
      <p>Saved</p>
      <SparkButton
        bookId="preview"
        chapterId="saved"
        chapterTitle="How I decided between two offers"
        sparkId="preview-spark"
      />
      <p>Saved, no book yet</p>
      <SparkButton
        bookId="preview"
        chapterId="saved-no-book"
        chapterTitle="How I decided between two offers"
        sparkId="preview-spark"
        hasBook={false}
      />
    </main>
  );
}
