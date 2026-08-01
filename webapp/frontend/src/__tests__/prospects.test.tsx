// prospects.test.tsx — filtrage de la table des prospects.

import { describe, expect, it } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { Prospects } from "../pages/Prospects";

function renderProspects() {
  return render(
    <MemoryRouter>
      <Prospects />
    </MemoryRouter>,
  );
}

describe("Prospects (table filtrable)", () => {
  it("liste tous les prospects mock au chargement", async () => {
    renderProspects();
    await waitFor(() =>
      expect(screen.getByText("Climatisation Tremblay")).toBeInTheDocument(),
    );
    // 8 prospects dans les fixtures.
    await waitFor(() => expect(screen.getByText(/8 résultats/)).toBeInTheDocument());
  });

  it("filtre par persona 2", async () => {
    const user = userEvent.setup();
    renderProspects();
    await waitFor(() =>
      expect(screen.getByText("Climatisation Tremblay")).toBeInTheDocument(),
    );

    await user.selectOptions(screen.getByLabelText("Persona"), "2");

    await waitFor(() => {
      // Persona 2 : seule "Agence Relance (Lyon)" reste.
      expect(screen.getByText("Agence Relance (Lyon)")).toBeInTheDocument();
      expect(screen.queryByText("Climatisation Tremblay")).not.toBeInTheDocument();
    });
    expect(screen.getByText(/1 résultat/)).toBeInTheDocument();
  });

  it("filtre par statut = decouvert", async () => {
    const user = userEvent.setup();
    renderProspects();
    await waitFor(() =>
      expect(screen.getByText("Climatisation Tremblay")).toBeInTheDocument(),
    );

    await user.selectOptions(screen.getByLabelText("Statut"), "decouvert");

    await waitFor(() => {
      expect(screen.getByText("HVAC Longueuil Services")).toBeInTheDocument();
      expect(screen.queryByText("Climatisation Tremblay")).not.toBeInTheDocument();
    });
  });

  it("trie par score descendant par défaut", async () => {
    renderProspects();
    await waitFor(() =>
      expect(screen.getByText("Climatisation Tremblay")).toBeInTheDocument(),
    );
    const rows = screen.getAllByRole("row");
    // rows[0] = header ; première ligne de données = plus haut score (88).
    const firstBody = within(rows[1]);
    expect(firstBody.getByText("88")).toBeInTheDocument();
  });
});
