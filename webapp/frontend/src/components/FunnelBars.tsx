// FunnelBars.tsx — entonnoir du pipeline en barres horizontales. Le flux normal
// (decouvert→diagnostique→valide→contacte) est séparé de rejete (barre crit).

import type { Funnel, Statut } from "../types";
import { STATUT_LABEL } from "../lib/format";
import { StatusPill } from "./StatusPill";

const FLUX: Statut[] = ["decouvert", "diagnostique", "valide", "contacte"];

export function FunnelBars({ funnel }: { funnel: Funnel }) {
  const values = funnel.etats;
  const max = Math.max(
    1,
    ...Object.values(values).map((v) => v),
  );

  const rows: Statut[] = [...FLUX, "rejete"];

  return (
    <div
      className="funnel"
      role="img"
      aria-label={`Entonnoir du pipeline, ${funnel.total} prospects au total`}
    >
      {rows.map((st) => {
        const n = values[st];
        const pct = Math.round((n / max) * 100);
        return (
          <div className="funnel-row" key={st}>
            <span className="lbl">
              <StatusPill statut={st} />
            </span>
            <div
              className={`funnel-bar ${st === "rejete" ? "rejete" : ""}`}
              aria-label={`${STATUT_LABEL[st]} : ${n}`}
            >
              <i style={{ width: `${Math.max(pct, n > 0 ? 4 : 0)}%` }} />
            </div>
            <span className="n num">{n}</span>
          </div>
        );
      })}
    </div>
  );
}
