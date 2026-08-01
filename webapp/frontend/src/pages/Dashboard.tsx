// Dashboard.tsx — vue de pilotage : verdict préflight, entonnoir, tuiles de
// coûts, raccourci vers les prospects à plus fort signal.

import { Link } from "react-router-dom";
import { api } from "../api";
import { useAsync } from "../hooks/useAsync";
import { AsyncView } from "../components/AsyncState";
import { VerdictBanner } from "../components/VerdictBanner";
import { FunnelBars } from "../components/FunnelBars";
import { StatTile } from "../components/StatTile";
import { StatusPill } from "../components/StatusPill";
import { fmtInt, fmtPct, fmtUsd, scoreClass } from "../lib/format";

export function Dashboard() {
  const preflight = useAsync(() => api.preflight(), []);
  const funnel = useAsync(() => api.funnel(), []);
  const usage = useAsync(() => api.usage(), []);
  const prospects = useAsync(() => api.prospects(), []);

  return (
    <div className="stack">
      <div className="page-head">
        <span className="eyebrow">Vue d'ensemble</span>
        <h1>Tableau de bord</h1>
        <p>
          État du pipeline de prospection, verdict de mise en route, et coûts API
          — en complément d'Obsidian.
        </p>
      </div>

      <AsyncView state={preflight} loadingLabel="Chargement du verdict…">
        {(data) => (
          <Link to="/preflight" aria-label="Voir le détail du préflight" style={{ textDecoration: "none" }}>
            <VerdictBanner preflight={data} />
          </Link>
        )}
      </AsyncView>

      <div className="grid grid-tiles">
        <AsyncView state={usage}>
          {(u) => (
            <>
              <StatTile
                label="Coût total"
                value={fmtUsd(u.cout_total_usd, u.devise)}
                sub={`${fmtInt(u.nb_appels)} appels API`}
              />
              <StatTile
                label="Taux de cache"
                value={fmtPct(u.taux_cache)}
                sub={`${fmtInt(u.nb_cache_hits)} hits économisés`}
              />
              <StatTile
                label="Fournisseurs"
                value={u.par_fournisseur.length}
                sub={u.par_fournisseur.map((f) => f.fournisseur).join(" · ")}
              />
            </>
          )}
        </AsyncView>
        <AsyncView state={funnel}>
          {(f) => (
            <StatTile
              label="Prospects au total"
              value={fmtInt(f.total)}
              sub={`${f.etats.valide} validés · ${f.etats.contacte} contactés`}
            />
          )}
        </AsyncView>
      </div>

      <div className="grid grid-2">
        <section className="panel panel-pad">
          <div className="panel-h">
            <h2>Entonnoir du pipeline</h2>
            <Link className="sub" to="/prospects">
              tout voir →
            </Link>
          </div>
          <AsyncView state={funnel}>{(f) => <FunnelBars funnel={f} />}</AsyncView>
        </section>

        <section className="panel panel-pad">
          <div className="panel-h">
            <h2>Signaux chauds</h2>
            <span className="sub">score le plus bas = priorité</span>
          </div>
          <AsyncView state={prospects}>
            {(list) => {
              const hot = list
                .filter((p) => p.signal_chaud && !p.opt_out)
                .sort((a, b) => (a.score_global ?? 999) - (b.score_global ?? 999))
                .slice(0, 5);
              if (hot.length === 0)
                return <div className="state-box">Aucun signal chaud actif.</div>;
              return (
                <div className="stack" style={{ gap: 8 }}>
                  {hot.map((p) => (
                    <Link
                      key={p.slug}
                      to={`/prospects/${p.slug}`}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: 12,
                        padding: "8px 10px",
                        border: "1px solid var(--line)",
                        borderRadius: 8,
                        textDecoration: "none",
                        color: "var(--ink)",
                      }}
                    >
                      <span className={`score ${scoreClass(p.score_global)}`}>
                        {p.score_global ?? "—"}
                      </span>
                      <span style={{ flex: 1, minWidth: 0 }}>
                        <div className="rowname">{p.nom}</div>
                        <div className="rowsub">
                          {p.marche} · persona {p.persona}
                        </div>
                      </span>
                      <StatusPill statut={p.statut} />
                    </Link>
                  ))}
                </div>
              );
            }}
          </AsyncView>
        </section>
      </div>
    </div>
  );
}
