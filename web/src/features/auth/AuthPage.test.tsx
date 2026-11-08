import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { AuthPage } from "./AuthPage";
import { AuthProvider } from "./AuthProvider";

function renderPage(mode: "sign-in" | "sign-up") {
  render(
    <AuthProvider>
      <MemoryRouter>
        <AuthPage mode={mode} />
      </MemoryRouter>
    </AuthProvider>,
  );
}

describe("AuthPage", () => {
  it("asks for a first and last name when signing up", () => {
    renderPage("sign-up");
    expect(screen.getByLabelText("First name")).toBeTruthy();
    expect(screen.getByLabelText("Last name")).toBeTruthy();
  });

  it("doesn't ask for a name when signing in", () => {
    renderPage("sign-in");
    expect(screen.queryByLabelText("First name")).toBeNull();
    expect(screen.queryByLabelText("Last name")).toBeNull();
  });
});
