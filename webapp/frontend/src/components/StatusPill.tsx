// StatusPill.tsx — pastille de statut : l'état se lit à la FORME (glyphe) autant
// qu'à la couleur, pour lisibilité daltonienne.

import type { Statut } from "../types";
import { STATUT_LABEL } from "../lib/format";

export function StatusPill({ statut }: { statut: Statut }) {
  return (
    <span className={`pill st-${statut}`} title={STATUT_LABEL[statut]}>
      <span className="glyph" aria-hidden="true" />
      {STATUT_LABEL[statut]}
    </span>
  );
}
