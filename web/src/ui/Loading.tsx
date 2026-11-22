import {
  createContext,
  type ReactNode,
  useCallback,
  useContext,
  useEffect,
  useLayoutEffect,
  useState,
} from "react";
import "./Loading.css";

// Pages appear whole, not piece by piece (docs/design/system.md, Additions, "Loading").
//
// A page that is still fetching what it needs renders <PageLoading /> in place of its content. While any
// <PageLoading /> is mounted, the screen stays hidden; once none is, it waits for the fonts (the first time
// only) and shows everything at once. If that takes longer than SLOW_MS, a quiet still placeholder shows in the
// meantime, so a fast page never flashes one. After GIVE_UP_MS the screen shows anyway, so nothing can hide it
// for good. The top bar waits with the first page, then stays up while later pages load under it.

const SLOW_MS = 200;
const GIVE_UP_MS = 10_000;
const FONTS_MS = 1_000;

const Register = createContext<() => () => void>(() => () => undefined);

let fontsSettled = false;
async function fontsReady(): Promise<void> {
  if (fontsSettled || typeof document === "undefined" || !document.fonts) return;
  await Promise.race([document.fonts.ready, new Promise((done) => setTimeout(done, FONTS_MS))]);
  fontsSettled = true;
}

export function LoadingGate({ children }: { children: ReactNode }) {
  const [pending, setPending] = useState(0);
  const [shown, setShown] = useState(false);
  const [slow, setSlow] = useState(false);
  // After the first screen, the top bar stays up while later pages load under it.
  const [settled, setSettled] = useState(false);

  const register = useCallback(() => {
    setPending((count) => count + 1);
    return () => setPending((count) => count - 1);
  }, []);

  useEffect(() => {
    let live = true;
    if (pending > 0) {
      setShown(false);
      const slowTimer = setTimeout(() => live && setSlow(true), SLOW_MS);
      const giveUp = setTimeout(() => {
        if (!live) return;
        setShown(true);
        setSettled(true);
      }, GIVE_UP_MS);
      return () => {
        live = false;
        clearTimeout(slowTimer);
        clearTimeout(giveUp);
      };
    }
    fontsReady().then(() => {
      if (!live) return;
      setShown(true);
      setSlow(false);
      setSettled(true);
    });
    return () => {
      live = false;
    };
  }, [pending]);

  return (
    <Register.Provider value={register}>
      <div
        className="loading-root"
        data-hidden={shown ? undefined : "true"}
        data-settled={settled ? "true" : undefined}
      >
        {children}
      </div>
      {slow && !shown && <LoadingScreen />}
    </Register.Provider>
  );
}

/** Rendered by a page while it fetches what it needs to show: keeps the screen hidden until it's ready. */
export function PageLoading() {
  const register = useContext(Register);
  // Before paint, so the page's empty frame never shows for even one frame.
  useLayoutEffect(() => register(), [register]);
  return null;
}

// Still, not a spinner: nothing animates on load or loops (docs/design/system.md).
function LoadingScreen() {
  return (
    <div className="loading-screen">
      <p role="status" className="loading-say">
        Loading
      </p>
      <div className="loading-title skeleton" />
      <div className="loading-blocks">
        <div className="skeleton" />
        <div className="skeleton" />
      </div>
    </div>
  );
}
