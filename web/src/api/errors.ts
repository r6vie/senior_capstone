// Turn a FastAPI error body ({"detail": ...}) into one sentence a member can read.
export function errorMessage(error: unknown): string {
  if (!error || typeof error !== "object" || !("detail" in error)) {
    return "Something went wrong. Please try again.";
  }
  const { detail } = error as { detail: unknown };
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((issue: { loc?: unknown[]; msg?: string }) => {
        const field = issue.loc?.at(-1);
        // Pydantic starts the message of our own validators with "Value error, ": a member shouldn't see that.
        const message = (issue.msg ?? "Invalid value.").replace(/^Value error, /, "");
        return `${typeof field === "string" ? `${field}: ` : ""}${message}`;
      })
      .join(" ");
  }
  return "Something went wrong. Please try again.";
}
