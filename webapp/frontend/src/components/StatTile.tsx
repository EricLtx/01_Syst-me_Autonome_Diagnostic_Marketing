// StatTile.tsx — tuile de chiffre-clé (KPI) pour le dashboard et l'usage.

import type { ReactNode } from "react";

interface StatTileProps {
  label: string;
  value: ReactNode;
  unit?: string;
  sub?: ReactNode;
}

export function StatTile({ label, value, unit, sub }: StatTileProps) {
  return (
    <div className="tile">
      <span className="k">{label}</span>
      <span className="v num">
        {value}
        {unit ? <span className="unit">{unit}</span> : null}
      </span>
      {sub ? <span className="sub">{sub}</span> : null}
    </div>
  );
}
