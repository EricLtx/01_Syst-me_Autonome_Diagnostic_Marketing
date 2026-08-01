// Usage.tsx — détail des coûts API : tuiles, table + barres par fournisseur,
// top fiches, taux de cache.

import { api } from "../api";
import { useAsync } from "../hooks/useAsync";
import { AsyncView } from "../components/AsyncState";
import { StatTile } from "../components/StatTile";
import { fmtInt, fmtPct, fmtUsd } from "../lib/format";

export function Usage() {
  const state = useAsync(() => api.usage(), []);

  return (
    <div className="stack">
      <div className="page-head">
        <span className="eyebrow">Grand livre</span>
        <h1>Coûts API</h1>
        <p>
          Agrégat de <code>api_usage.log</code> : source de vérité des coûts
          (tokens Claude, crédits Places, requêtes SERP).
        </p>
      </div>

      <AsyncView state={state}>
        {(u) => {
          const maxCost = Math.max(1, ...u.par_fournisseur.map((f) => f.cout_total));
          const maxFiche = Math.max(1, ...u.top_fiches.map((f) => f.cout));
          return (
            <>
              <div className="grid grid-tiles">
                <StatTile
                  label="Coût total"
                  value={fmtUsd(u.cout_total_usd, u.devise)}
                  sub={u.devise}
                />
                <StatTile label="Appels API" value={fmtInt(u.nb_appels)} />
                <StatTile
                  label="Taux de cache"
                  value={fmtPct(u.taux_cache)}
                  sub={`${fmtInt(u.nb_cache_hits)} hits`}
                />
                <StatTile label="Fournisseurs" value={u.par_fournisseur.length} />
              </div>

              <div className="grid grid-2">
                <section className="panel panel-pad">
                  <div className="panel-h">
                    <h2>Par fournisseur</h2>
                    <span className="sub">coût cumulé</span>
                  </div>
                  <div className="tablewrap" style={{ boxShadow: "none", border: "none" }}>
                    <table className="data" style={{ minWidth: 420 }}>
                      <thead>
                        <tr>
                          <th scope="col">Fournisseur</th>
                          <th scope="col" className="num">Appels</th>
                          <th scope="col" className="num">Unités</th>
                          <th scope="col" className="num">Coût</th>
                        </tr>
                      </thead>
                      <tbody>
                        {u.par_fournisseur.map((f) => (
                          <tr key={f.fournisseur} style={{ cursor: "default" }}>
                            <td>
                              <div className="rowname mono">{f.fournisseur}</div>
                              <div
                                className="bartrack"
                                style={{ marginTop: 5, maxWidth: 160 }}
                                aria-label={`${f.fournisseur} : ${fmtUsd(f.cout_total, u.devise)}`}
                              >
                                <i style={{ width: `${(f.cout_total / maxCost) * 100}%` }} />
                              </div>
                            </td>
                            <td className="num">{fmtInt(f.nb_appels)}</td>
                            <td className="num">{fmtInt(f.unites)}</td>
                            <td className="num">{fmtUsd(f.cout_total, u.devise)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </section>

                <section className="panel panel-pad">
                  <div className="panel-h">
                    <h2>Top fiches par coût</h2>
                    <span className="sub">les plus gourmandes</span>
                  </div>
                  <div className="stack" style={{ gap: 10 }}>
                    {u.top_fiches.map((f) => (
                      <div key={f.fiche}>
                        <div
                          style={{
                            display: "flex",
                            justifyContent: "space-between",
                            fontSize: 13,
                            marginBottom: 4,
                          }}
                        >
                          <span className="mono">{f.fiche}</span>
                          <span className="num mono">{fmtUsd(f.cout, u.devise)}</span>
                        </div>
                        <div
                          className="bartrack"
                          aria-label={`${f.fiche} : ${fmtUsd(f.cout, u.devise)}`}
                        >
                          <i style={{ width: `${(f.cout / maxFiche) * 100}%` }} />
                        </div>
                      </div>
                    ))}
                  </div>
                </section>
              </div>
            </>
          );
        }}
      </AsyncView>
    </div>
  );
}
