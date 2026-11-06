import { Button } from "../../ui/Button";
import { useAuth } from "../auth/AuthProvider";

// Placeholder until the book and interview features exist.
export function HomePage() {
  const { user, signOut } = useAuth();
  return (
    <main className="narrow-page">
      <h1>Hi {user?.first_name}.</h1>
      <p className="muted">Your book is coming soon.</p>
      <Button variant="secondary" onClick={signOut}>
        Sign out
      </Button>
    </main>
  );
}
