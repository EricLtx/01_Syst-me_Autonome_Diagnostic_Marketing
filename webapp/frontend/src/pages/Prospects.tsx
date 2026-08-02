// Prospects.tsx — table filtrable (statut / persona / marché), tri par score,
// clic sur une ligne -> détail.

import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import { useAsync } from "../hooks/useAsync";
import { AsyncView } from "../components/AsyncState";
import { StatusPill } from "../components/StatusPill";
import { STATUTS, STATUT_LABEL, fmtDate, scoreClass } from "../lib/format";
import type { Prospect, Statut } from "../types";

type SortDir = "asc" | "desc";

export function Prospects() {
  const navigate = useNavigate();
  const state = useAsync(() => api.prospects(), []);
  const icps = useAsync(() => api.icp(), []);

  const [statut, setStatut] = useState<Statut | "">("");
  const [persona, setPersona] = useState<string>("");
  const [marche, setMarche] = useState<string>("");
  const [sortDir, setSortDir] = useState<SortDir>("desc");

  const marches = useMemo(() => {
    const set = new Set((icps.data ?? []).map((i) => i.marche));
    (state.data ?? []).forEach((p) => set.add(p.marche));
    return [...set].sort();
  }, [icps.data, state.data]);

  const rows = useMemo(() => {
    let list: Prospect[] = state.data ?? [];
    if (statut) list = list.filter((p) => p.statut === statut);
    if (persona) list = list.filter((p) => String(p.persona) === persona);
    if (marche) list = list.filter((p) => p.marche === marche);
    // Tri par score ; les scores nuls (non diagnostiqués) en fin de liste.
    list = [...list].sort((a, b) => {
      const av = a.score_global ?? -1;
      const bv = b.score_global ?? -1;
      return sortDir === "desc" ? bv - av : av - bv;
    });
    return list;
  }, [state.data, statut, persona, marche, sortDir]);

  return (
    <div className="stack">
      <div className="page-head">
        <span className="eyebrow">Pipeline</span>
        <h1>Prospects</h1>
        <p>
          Tri par score de diagnostic. Les fiches en opt-out sont marquées et
          exclues des exports.
        </p>
      </div>

      <div className="filters">
        <div className="field">
          <label htmlFor="f-statut">Statut</label>
          <select
            id="f-statut"
            value={statut}
            onChange={(e) => setStatut(e.target.value as Statut | "")}
          >
            <option value="">Tous</option>
            {STATUTS.map((s) => (
              <option key={s} value={s}>
                {STATUT_LABEL[s]}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label htmlFor="f-persona">Persona</label>
          <select
            id="f-persona"
            value={persona}
            onChange={(e) => setPersona(e.target.value)}
          >
            <option value="">Tous</option>
            <option value="1">Persona 1</option>
            <option value="2">Persona 2</option>
          </select>
        </div>
        <div className="field">
          <label htmlFor="f-marche">Marché</label>
          <select
            id="f-marche"
            value={marche}
            onChange={(e) => setMarche(e.target.value)}
          >
            <option value="">Tous</option>
            {marches.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
        </div>
        <span className="count num" aria-live="polite">
          {rows.length} résultat{rows.length > 1 ? "s" : ""}
        </span>
      </div>

      <AsyncView state={state}>
        {() =>
          rows.length === 0 ? (
            <div className="state-box">Aucun prospect ne correspond aux filtres.</div>
          ) : (
            <div className="tablewrap">
              <table className="data">
                <thead>
                  <tr>
                    <th scope="col">Nom</th>
                    <th scope="col">Statut</th>
                    <th
                      scope="col"
                      className="num sortable"
                      onClick={() =>
                        setSortDir((d) => (d === "desc" ? "asc" : "desc"))
                      }
                      aria-sort={sortDir === "desc" ? "descending" : "ascending"}
                    >
                      Score <span className="arrow">{sortDir === "desc" ? "▾" : "▴"}</span>
                    </th>
                    <th scope="col">Signal</th>
                    <th scope="col">Marché</th>
                    <th scope="col">Opt-out</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((p) => (
                    <tr
                      key={p.slug}
                      tabIndex={0}
                      onClick={() => navigate(`/prospects/${p.slug}`)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") navigate(`/prospects/${p.slug}`);
                      }}
                    >
                      <td>
                        <div className="rowname">{p.nom}</div>
                        <div className="rowsub mono">{p.slug}</div>
                      </td>
                      <td>
                        <StatusPill statut={p.statut} />
                      </td>
                      <td className="num">
                        <span className={`score ${scoreClass(p.score_global)}`}>
                          {p.score_global ?? "—"}
                        </span>
                      </td>
                      <td>
                        {p.signal_chaud ? (
                          <span className="tag hot">chaud</span>
                        ) : (
                          <span className="muted">—</span>
                        )}
                      </td>
                      <td>
                        <span className="mono" style={{ fontSize: 12 }}>
                          {p.marche}
                        </span>
                        <div className="rowsub">
                          {p.persona != null ? `persona ${p.persona} · ` : ""}{fmtDate(p.date_diagnostic)}
                        </div>
                      </td>
                      <td>
                        {p.opt_out ? (
                          <span className="tag optout">opt-out</span>
                        ) : (
                          <span className="muted">—</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )
        }
      </AsyncView>
    </div>
  );
}
