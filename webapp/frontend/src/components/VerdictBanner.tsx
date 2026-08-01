// VerdictBanner.tsx — bandeau GO / NO-GO du préflight (pastille sémantique).

import type { Preflight } from "../types";

export function VerdictBanner({ preflight }: { preflight: Preflight }) {
  const go = preflight.verdict === "GO";
  const bloquants = preflight.checks.filter(
    (c) => c.niveau === "bloquant" && !c.ok,
  ).length;
  const warns = preflight.checks.filter((c) => c.niveau === "warn" && !c.ok).length;

  return (
    <div
      className={`verdict ${go ? "go" : "nogo"}`}
      role="status"
      aria-label={`Verdict préflight : ${preflight.verdict}`}
    >
      <span className="lamp" aria-hidden="true">
        {go ? "GO" : "NO"}
      </span>
      <span className="vtext">
        <span className="k">Verdict préflight</span>
        <span className="v">{go ? "GO — prêt au run réel" : "NO-GO — run bloqué"}</span>
      </span>
      <span className="vmeta">
        <div>
          <b className="num">{bloquants}</b> bloquant{bloquants > 1 ? "s" : ""} en
          échec
        </div>
        <div>
          <b className="num">{warns}</b> avertissement{warns > 1 ? "s" : ""}
        </div>
      </span>
    </div>
  );
}
