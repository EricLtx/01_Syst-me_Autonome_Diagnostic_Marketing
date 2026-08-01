// api.test.ts — le client en MODE MOCK renvoie les fixtures sans réseau.

import { describe, expect, it } from "vitest";
import { api, USE_MOCKS } from "../api";

describe("client api (mode mock)", () => {
  it("est en mode mock par défaut dans les tests", () => {
    expect(USE_MOCKS).toBe(true);
  });

  it("renvoie un préflight NO-GO reflétant l'AS-IS", async () => {
    const pf = await api.preflight();
    expect(pf.verdict).toBe("NO-GO");
    // Au moins un bloquant en échec (clés API absentes).
    const bloquantsKO = pf.checks.filter((c) => c.niveau === "bloquant" && !c.ok);
    expect(bloquantsKO.length).toBeGreaterThan(0);
    // tests_verts est un warn qui passe.
    const testsVerts = pf.checks.find((c) => c.nom === "tests_verts");
    expect(testsVerts?.niveau).toBe("warn");
    expect(testsVerts?.ok).toBe(true);
  });

  it("renvoie un funnel cohérent avec la somme des états", async () => {
    const f = await api.funnel();
    const somme =
      f.etats.decouvert +
      f.etats.diagnostique +
      f.etats.valide +
      f.etats.contacte +
      f.etats.rejete;
    expect(somme).toBe(f.total);
  });

  it("filtre les prospects par persona côté client mock", async () => {
    const tous = await api.prospects();
    const p2 = await api.prospects({ persona: 2 });
    expect(tous.length).toBeGreaterThan(p2.length);
    expect(p2.every((p) => p.persona === 2)).toBe(true);
  });

  it("expose au moins un rapport Markdown", async () => {
    const detail = await api.prospect("climatisation-tremblay");
    expect(detail.rapport_md).toContain("# Audit de marque");
  });

  it("couvre tous les statuts et 2 personas dans les fixtures", async () => {
    const list = await api.prospects();
    const statuts = new Set(list.map((p) => p.statut));
    expect(statuts).toEqual(
      new Set(["decouvert", "diagnostique", "valide", "contacte", "rejete"]),
    );
    expect(new Set(list.map((p) => p.persona))).toEqual(new Set([1, 2]));
  });
});
