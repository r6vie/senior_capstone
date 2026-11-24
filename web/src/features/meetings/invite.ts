import { api } from "../../api/client";
import { errorMessage } from "../../api/errors";

/**
 * Saves the meeting's calendar file (.ics). It needs the signed-in request, so a plain link won't do: fetch it,
 * then save it. Returns a sentence to show if it failed, or null.
 */
export async function downloadInvite(checkoutId: string): Promise<string | null> {
  let failure: unknown;
  let file: Blob | undefined;
  try {
    const { data, error } = await api.GET("/meetings/{checkout_id}/invite.ics", {
      params: { path: { checkout_id: checkoutId } },
      parseAs: "blob",
    });
    file = data as Blob | undefined;
    failure = error;
  } catch {
    failure = { detail: "We couldn't get the calendar file. Check your connection and try again." };
  }
  if (!file) return errorMessage(failure);
  const url = URL.createObjectURL(file);
  const link = document.createElement("a");
  link.href = url;
  link.download = "trove-meeting.ics";
  link.click();
  URL.revokeObjectURL(url);
  return null;
}
