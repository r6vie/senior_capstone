import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./app/App";
import { ErrorBoundary, PageBroke } from "./ui/ErrorBoundary";
import "./ui/styles.css";

const root = document.getElementById("root");
if (!root) throw new Error("index.html is missing the #root element.");

createRoot(root).render(
  <StrictMode>
    {/* The last net, outside the router: a plain link home reloads the app from scratch. */}
    <ErrorBoundary
      fallback={(retry) => (
        <PageBroke
          retry={retry}
          home={
            <a className="button button-quiet" href="/">
              Go to the shelf
            </a>
          }
        />
      )}
    >
      <App />
    </ErrorBoundary>
  </StrictMode>,
);
