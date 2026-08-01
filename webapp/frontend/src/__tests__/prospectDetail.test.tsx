// prospectDetail.test.tsx — détail avec rendu Markdown du rapport + mention RGPD.

import { describe, expect, it } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { ProspectDetail } from "../pages/ProspectDetail";
import { renderMarkdown } from "../lib/markdown";

function renderDetail(slug: string) {
  return render(
    <MemoryRouter initialEntries={[`/prospects/${slug}`]}>
      <Routes>
        <Route path="/prospects/:slug" element={<ProspectDetail />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("ProspectDetail", () => {
  it("rend le rapport Markdown (titre + tableau)", async () => {
    renderDetail("climatisation-tremblay");
    await waitFor(() =>
      expect(
        screen.getByRole("heading", { name: /Audit de marque/i }),
      ).toBeInTheDocument(),
    );
    // Un tableau GFM du rapport doit être rendu comme <table>.
    expect(screen.getAllByRole("table").length).toBeGreaterThan(0);
    // La mention RGPD apparaît car un email de contact est présent.
    expect(screen.getByText(/intérêt légitime B2B/i)).toBeInTheDocument();
  });

  it("affiche un message quand aucun rapport n'est disponible", async () => {
    renderDetail("hvac-longueuil");
    await waitFor(() =>
      expect(screen.getByText(/Aucun rapport généré/i)).toBeInTheDocument(),
    );
  });
});

describe("renderMarkdown (rendu sûr)", () => {
  it("ne produit pas de HTML brut à partir d'une injection", () => {
    const { container } = render(
      <div>{renderMarkdown("Bonjour <img src=x onerror=alert(1)> **gras**")}</div>,
    );
    // Aucune balise <img> injectée : le texte reste échappé.
    expect(container.querySelector("img")).toBeNull();
    expect(container.textContent).toContain("<img src=x onerror=alert(1)>");
    // Le gras Markdown est bien interprété.
    expect(container.querySelector("strong")?.textContent).toBe("gras");
  });

  it("convertit un tableau GFM en <table>", () => {
    const md = "| A | B |\n|---|---|\n| 1 | 2 |";
    const { container } = render(<div>{renderMarkdown(md)}</div>);
    expect(container.querySelector("table")).not.toBeNull();
    expect(container.querySelectorAll("td").length).toBe(2);
  });
});
