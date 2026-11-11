import { errorMessage } from "./errors";

describe("errorMessage", () => {
  it("passes plain messages through", () => {
    expect(errorMessage({ detail: "Incorrect email or password." })).toBe("Incorrect email or password.");
  });

  it("names the field for validation errors", () => {
    const body = { detail: [{ loc: ["body", "password"], msg: "Too short" }] };
    expect(errorMessage(body)).toBe("password: Too short");
  });

  it('drops pydantic\'s "Value error" prefix from our own validators', () => {
    const body = { detail: [{ loc: ["body", "phone"], msg: "Value error, Enter a phone number." }] };
    expect(errorMessage(body)).toBe("phone: Enter a phone number.");
  });

  it("falls back for anything else", () => {
    expect(errorMessage(undefined)).toBe("Something went wrong. Please try again.");
  });
});
