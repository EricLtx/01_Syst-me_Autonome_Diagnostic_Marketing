// Layout.tsx — coquille persistante : navigation latérale + zone de contenu.

import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";
import { ThemeToggle } from "./ThemeToggle";
import { USE_MOCKS } from "../api";

const LINKS = [
  { to: "/", label: "Tableau de bord", end: true },
  { to: "/prospects", label: "Prospects", end: false },
  { to: "/usage", label: "Coûts API", end: false },
  { to: "/preflight", label: "Préflight", end: false },
];

export function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="eyebrow">Diagnostic marketing</span>
          <span className="title">Cockpit opérateur</span>
        </div>
        <nav className="nav" aria-label="Navigation principale">
          {LINKS.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.end}
              className={({ isActive }) => (isActive ? "active" : "")}
            >
              <span className="dot" aria-hidden="true" />
              {l.label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-foot">
          {USE_MOCKS ? (
            <div className="mockbadge" title="Données de démonstration (fixtures locales)">
              Mode mock
            </div>
          ) : null}
          <ThemeToggle />
        </div>
      </aside>
      <main className="main">{children}</main>
    </div>
  );
}
