// ThemeToggle.tsx — bascule clair/sombre. Par défaut on suit le système ; le
// toggle pose data-theme sur :root (qui l'emporte sur prefers-color-scheme).

import { useEffect, useState } from "react";

type Mode = "auto" | "light" | "dark";
const KEY = "cockpit-theme";

function apply(mode: Mode) {
  const root = document.documentElement;
  if (mode === "auto") root.removeAttribute("data-theme");
  else root.setAttribute("data-theme", mode);
}

export function ThemeToggle() {
  const [mode, setMode] = useState<Mode>(() => {
    const saved = (typeof localStorage !== "undefined" &&
      localStorage.getItem(KEY)) as Mode | null;
    return saved ?? "auto";
  });

  useEffect(() => {
    apply(mode);
    try {
      localStorage.setItem(KEY, mode);
    } catch {
      /* stockage indisponible : on ignore */
    }
  }, [mode]);

  const next: Record<Mode, Mode> = {
    auto: "light",
    light: "dark",
    dark: "auto",
  };
  const label: Record<Mode, string> = {
    auto: "Auto",
    light: "Clair",
    dark: "Sombre",
  };
  const glyph: Record<Mode, string> = {
    auto: "◑",
    light: "○",
    dark: "●",
  };

  return (
    <button
      type="button"
      className="theme-toggle"
      onClick={() => setMode(next[mode])}
      aria-label={`Thème : ${label[mode]}. Cliquer pour changer.`}
    >
      <span aria-hidden="true">{glyph[mode]}</span>
      Thème · {label[mode]}
    </button>
  );
}
