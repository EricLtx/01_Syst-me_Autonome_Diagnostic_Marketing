// dashboard.test.tsx — rendu du Dashboard avec mocks : verdict + funnel.

import { describe, expect, it } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { Dashboard } from "../pages/Dashboard";

function renderDashboard() {
  return render(
    <MemoryRouter>
      <Dashboard />
    </MemoryRouter>,
  );
}

describe("Dashboard", () => {
  it("affiche le titre et charge le verdict NO-GO", async () => {
    renderDashboard();
    expect(screen.getByRole("heading", { name: /Tableau de bord/i })).toBeInTheDocument();
    await waitFor(() =>
      expect(screen.getByText(/NO-GO/)).toBeInTheDocument(),
    );
  });

  it("affiche l'entonnoir avec les 5 états du pipeline", async () => {
    renderDashboard();
    await waitFor(() =>
      expect(
        screen.getByRole("img", { name: /Entonnoir du pipeline/i }),
      ).toBeInTheDocument(),
    );
    // Le total (34) apparaît dans une tuile.
    await waitFor(() => expect(screen.getByText("34")).toBeInTheDocument());
  });

  it("affiche les tuiles de coûts (coût total en USD)", async () => {
    renderDashboard();
    await waitFor(() => expect(screen.getByText(/Coût total/i)).toBeInTheDocument());
    await waitFor(() => expect(screen.getByText(/\$12\.47/)).toBeInTheDocument());
  });
});
