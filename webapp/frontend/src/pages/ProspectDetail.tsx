// ProspectDetail.tsx — fiche complète + rendu Markdown du rapport de diagnostic.
// Contact affiché avec mention RGPD si email présent ; gaps majeurs et accroche.

import { Link, useParams } from "react-router-dom";
import { api } from "../api";
import { useAsync } from "../hooks/useAsync";
import { AsyncView } from "../components/AsyncState";
import { StatusPill } from "../components/StatusPill";
import { renderMarkdown } from "../lib/markdown";
import { fmtDate, scoreClass } from "../lib/format";
import type { Prospect } from "../types";

function readStr(fiche: Record<string, unknown>, key: string): string | null {
  const v = fiche[key];
  return typeof v === "string" && v.length > 0 ? v : null;
}

export function ProspectDetail() {
  const { slug = "" } = useParams();
  const state = useAsync(() => api.prospect(slug), [slug]);

  return (
    <div className="stack">
      <div className="crumb">
        <Link to="/prospects">Prospects</Link> / {slug}
      </div>

      <AsyncView state={state} loadingLabel="Chargement de la fiche…">
        {(detail) => {
          const p = detail.fiche as Prospect & Record<string, unknown>;
          const accroche = readStr(detail.fiche, "accroche");
          const emailSource = readStr(detail.fiche, "source_email");
          return (
            <>
              <div className="page-head" style={{ marginBottom: 8 }}>
                <span className="eyebrow">
                  {p.icp_id} · persona {p.persona}
                </span>
                <h1>{p.nom}</h1>
                <p style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
                  <StatusPill statut={p.statut} />
                  <span className={`score ${scoreClass(p.score_global)}`}>
                    {p.score_global ?? "—"}
                  </span>
                  {p.signal_chaud ? <span className="tag hot">signal chaud</span> : null}
                  {p.opt_out ? <span className="tag optout">opt-out</span> : null}
                  {p.site_web ? (
                    <a href={p.site_web} target="_blank" rel="noopener noreferrer">
                      {p.site_web.replace(/^https?:\/\//, "")}
                    </a>
                  ) : null}
                </p>
              </div>

              <div className="grid grid-2">
                <section className="panel panel-pad">
                  <div className="panel-h">
                    <h2>Fiche</h2>
                    <span className="sub">{p.marche}</span>
                  </div>
                  <dl className="kv">
                    <dt>Statut</dt>
                    <dd>
                      <StatusPill statut={p.statut} />
                    </dd>
                    <dt>Score global</dt>
                    <dd className="num mono">{p.score_global ?? "non diagnostiqué"}</dd>
                    <dt>Marché</dt>
                    <dd>{p.marche}</dd>
                    <dt>ICP</dt>
                    <dd className="mono">{p.icp_id}</dd>
                    <dt>Créé le</dt>
                    <dd className="mono num">{fmtDate(p.date_creation)}</dd>
                    <dt>Diagnostiqué le</dt>
                    <dd className="mono num">{fmtDate(p.date_diagnostic)}</dd>
                  </dl>

                  <div className="spacer" />
                  <div className="panel-h">
                    <h2 style={{ fontSize: 13 }}>Contact</h2>
                  </div>
                  {p.contact_nom || p.contact_email ? (
                    <dl className="kv">
                      <dt>Nom</dt>
                      <dd>{p.contact_nom ?? "—"}</dd>
                      <dt>Email</dt>
                      <dd>{p.contact_email ?? "—"}</dd>
                      {p.contact_email ? (
                        <>
                          <dt>RGPD</dt>
                          <dd className="rgpd">
                            Donnée personnelle · base : intérêt légitime B2B
                            {emailSource ? ` · source : ${emailSource}` : ""}
                          </dd>
                        </>
                      ) : null}
                    </dl>
                  ) : (
                    <p className="muted">Aucun contact enrichi.</p>
                  )}
                </section>

                <section className="panel panel-pad">
                  <div className="panel-h">
                    <h2>Gaps majeurs</h2>
                    <span className="sub">{p.gaps_majeurs.length} identifié{p.gaps_majeurs.length > 1 ? "s" : ""}</span>
                  </div>
                  {p.gaps_majeurs.length > 0 ? (
                    <div className="chips">
                      {p.gaps_majeurs.map((g) => (
                        <span className="gap-chip" key={g}>
                          {g}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <p className="muted">Aucun gap majeur enregistré.</p>
                  )}

                  {accroche ? (
                    <>
                      <div className="spacer" />
                      <div className="panel-h">
                        <h2 style={{ fontSize: 13 }}>Accroche</h2>
                      </div>
                      <blockquote
                        style={{
                          margin: 0,
                          padding: "10px 14px",
                          borderLeft: "3px solid var(--accent)",
                          background: "var(--accent-soft)",
                          borderRadius: "0 8px 8px 0",
                          fontSize: 13.5,
                        }}
                      >
                        {accroche}
                      </blockquote>
                    </>
                  ) : null}
                </section>
              </div>

              <section className="panel panel-pad">
                <div className="panel-h">
                  <h2>Rapport de diagnostic</h2>
                  <span className="sub">Markdown</span>
                </div>
                {detail.rapport_md ? (
                  renderMarkdown(detail.rapport_md)
                ) : (
                  <div className="state-box">
                    Aucun rapport généré pour cette fiche (statut {p.statut}).
                  </div>
                )}
              </section>
            </>
          );
        }}
      </AsyncView>
    </div>
  );
}
