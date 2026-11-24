import { fireEvent } from "@testing-library/react";
import { textOf } from "./librarian/AnswerText";

// Tests type into the answer the same way whichever field it is: the Librarian's editable text, or a
// plain textarea where there's no Librarian (a reading question).

export function setAnswer(field: HTMLElement, text: string) {
  if (field instanceof HTMLTextAreaElement) {
    fireEvent.change(field, { target: { value: text } });
    return;
  }
  field.textContent = text;
  fireEvent.input(field);
}

export function answerOf(field: HTMLElement): string {
  return field instanceof HTMLTextAreaElement ? field.value : textOf(field);
}
