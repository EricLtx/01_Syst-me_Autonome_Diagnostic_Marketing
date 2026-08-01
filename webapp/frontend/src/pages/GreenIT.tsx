// GreenIT.tsx — tableau de bord d'efficience (FinOps / GreenIT) alimenté en
// TEMPS RÉEL par le flux SSE du grand livre `api_usage.log`.
//
// Parti pris d'information design :
//   - les tuiles bougent en direct (agrégation incrémentale côté client) ;
//   - l'état de la liaison est toujours affiché — un cockpit ne doit jamais
//     laisser croire qu'il est « en direct » alors qu'il est figé ;
//   - énergie et CO2e sont ENCADRÉS d'un avertissement permanent : ce sont des
//     ESTIMATIONS paramétrables (knowledge/greenit.yaml), jamais des mesures.

import { useEffect, useState } from "react";
import { api, souscrireGreenit } from "../api";
import { useAsync } from "../hooks/useAsync";
import { ErrorBox, Loading } from "../components/AsyncState";
import { StatTile } from "../components/StatTile";
import { fmtInt, fmtPct, fmtUsd } from "../lib/format";
import {
  appliquerAppel,
  fmtCo2,
  fmtDuree,
  fmtHeure,
  fmtOctets,
  fmtWh,
} from "../lib/greenit";
import type { EtatFlux, Greenit, GreenitAppel } from "../types";

const MAX_FLUX = 40; // au-delà, on oublie : c'est un moniteur, pas une archive.

const ETAT_LABEL: Record<EtatFlux, string> = {
  connexion: "Connexion…",
  connecte: "En direct",
  polling: "Repli polling",
  deconnecte: "Déconnecté",
  termine: "Flux terminé",
};

function IndicateurFlux({ etat }: { etat: EtatFlux }) {
  return (
    <span className={`flux-etat e-${etat}`} role="status" aria-live="polite">
      <span className="glyph" aria-hidden="true" />
      {ETAT_LABEL[etat]}
    </span>
  );
}

/** Bandeau d'honnêteté méthodologique — non masquable, par conception. */
function AvertissementEstimation({ agregat }: { agregat: Greenit | null }) {
  return (
    <aside className="estim-note" role="note">
      <span className="badge">Estimation</span>
      <p>
        <strong>L’énergie (Wh) et le CO₂e (g) affichés ici sont des estimations</strong>,
        calculées à partir des facteurs paramétrables de{" "}
        <code>{agregat?.source_facteurs ?? "knowledge/greenit.yaml"}</code>. Ce sont
        des ordres de grandeur destinés à comparer des scénarios entre eux (avec
        ou sans cache, petit ou gros modèle) — <strong>pas</strong> des mesures
        certifiées, et en aucun cas un bilan carbone opposable. Le coût, lui, est
        calculé depuis la grille tarifaire <code>knowledge/api_pricing.yaml</code>.
        {agregat ? (
          <>
            {" "}
            Couverture de l’instrumentation :{" "}
            <b className="num">{fmtPct(agregat.couverture_greenit)}</b> des appels
            réels portent des champs d’empreinte ; les autres comptent pour zéro.
          </>
        ) : null}
      </p>
    </aside>
  );
}

interface LigneBarre {
  nom: string;
  nb_appels: number;
  tokens: number;
  cout: number;
  energie_wh: number;
  co2e_g: number;
  octets: number;
}

function PanneauBarres({
  titre,
  sousTitre,
  lignes,
  colonne,
}: {
  titre: string;
  sousTitre: string;
  lignes: LigneBarre[];
  colonne: string;
}) {
  const maxCout = Math.max(1e-9, ...lignes.map((l) => l.cout));
  return (
    <section className="panel panel-pad">
      <div className="panel-h">
        <h2>{titre}</h2>
        <span className="sub">{sousTitre}</span>
      </div>
      {lignes.length === 0 ? (
        <p className="muted" style={{ fontSize: 13, margin: 0 }}>
          Aucun appel journalisé.
        </p>
      ) : (
        <div className="tablewrap" style={{ boxShadow: "none", border: "none" }}>
          <table className="data" style={{ minWidth: 460 }}>
            <thead>
              <tr>
                <th scope="col">{colonne}</th>
                <th scope="col" className="num">
                  Appels
                </th>
                <th scope="col" className="num">
                  Coût
                </th>
                <th scope="col" className="num">
                  Wh <abbr title="estimation">~</abbr>
                </th>
                <th scope="col" className="num">
                  CO₂e <abbr title="estimation">~</abbr>
                </th>
              </tr>
            </thead>
            <tbody>
              {lignes.map((l) => (
                <tr key={l.nom} style={{ cursor: "default" }}>
                  <td>
                    <div className="rowname mono">{l.nom}</div>
                    <div
                      className="bartrack"
                      style={{ marginTop: 5, maxWidth: 180 }}
                      role="img"
                      aria-label={`${l.nom} : ${fmtUsd(l.cout)} de coût, ${fmtWh(
                        l.energie_wh,
                      )} estimés, ${fmtOctets(l.octets)} transférés`}
                    >
                      <i style={{ width: `${(l.cout / maxCout) * 100}%` }} />
                    </div>
                  </td>
                  <td className="num">{fmtInt(l.nb_appels)}</td>
                  <td className="num">{fmtUsd(l.cout)}</td>
                  <td className="num">{fmtWh(l.energie_wh)}</td>
                  <td className="num">{fmtCo2(l.co2e_g)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

function classeResultat(a: GreenitAppel): string {
  if (a.cache_hit) return "r-cache";
  if (a.resultat === "erreur") return "r-erreur";
  if (a.resultat === "budget_depasse") return "r-budget";
  return "r-ok";
}

function libelleResultat(a: GreenitAppel): string {
  if (a.cache_hit) return "cache";
  if (a.resultat === "budget_depasse") return "budget";
  return a.resultat;
}

export function GreenIT() {
  const initial = useAsync(() => api.greenit(), []);
  const [agregat, setAgregat] = useState<Greenit | null>(null);
  const [flux, setFlux] = useState<GreenitAppel[]>([]);
  const [etat, setEtat] = useState<EtatFlux>("connexion");

  // L'agrégat initial vient de /api/greenit ; le flux le fait ensuite évoluer.
  useEffect(() => {
    if (initial.data) setAgregat(initial.data);
  }, [initial.data]);

  useEffect(() => {
    const abonnement = souscrireGreenit({
      onAppel: (appel) => {
        setFlux((precedent) => [appel, ...precedent].slice(0, MAX_FLUX));
        setAgregat((courant) => (courant ? appliquerAppel(courant, appel) : courant));
      },
      onEtat: setEtat,
      // Repli polling : on remplace l'agrégat par celui du serveur.
      onAgregat: (frais) => setAgregat(frais),
    });
    return () => abonnement.fermer();
  }, []);

  return (
    <div className="stack">
      <div className="page-head">
        <span className="eyebrow">Efficience · temps réel</span>
        <h1>GreenIT</h1>
        <p>
          Coût, énergie, empreinte carbone et volume transféré de chaque appel
          d’API, lus en direct dans le grand livre <code>api_usage.log</code>.
          Objectif : rendre visible ce que le cache et le routage de modèle font
          économiser.
        </p>
      </div>

      <AvertissementEstimation agregat={agregat} />

      {initial.loading && !agregat ? <Loading label="Chargement de l’agrégat…" /> : null}
      {initial.error && !agregat ? <ErrorBox message={initial.error} /> : null}

      {agregat ? (
        <>
          <div className="grid grid-tiles">
            <StatTile
              label="Coût total"
              value={fmtUsd(agregat.cout_total_usd, agregat.devise)}
              sub={`${fmtInt(agregat.nb_appels)} appels réels`}
            />
            <StatTile
              label="Énergie ~"
              value={fmtWh(agregat.energie_wh_total)}
              sub="estimation"
            />
            <StatTile
              label="CO₂e ~"
              value={fmtCo2(agregat.co2e_g_total)}
              sub="estimation"
            />
            <StatTile
              label="Octets transférés"
              value={fmtOctets(agregat.octets_total)}
              sub={fmtDuree(agregat.duree_ms_totale)}
            />
            <StatTile
              label="Taux de cache"
              value={fmtPct(agregat.taux_cache)}
              sub={`${fmtInt(agregat.nb_cache_hits)} appels évités`}
            />
          </div>

          <section
            className="panel panel-pad eco"
            role="region"
            aria-label="Économies réalisées par le cache"
          >
            <div className="panel-h">
              <h2>Économies réalisées par le cache</h2>
              <span className="sub">estimation</span>
            </div>
            <div className="eco-grid">
              <div className="eco-item">
                <span className="k">Appels évités</span>
                <span className="v num">{fmtInt(agregat.economies.appels_evites)}</span>
              </div>
              <div className="eco-item">
                <span className="k">Coût évité</span>
                <span className="v num">
                  {fmtUsd(agregat.economies.cout_evite_usd, agregat.devise)}
                </span>
              </div>
              <div className="eco-item">
                <span className="k">Énergie évitée ~</span>
                <span className="v num">{fmtWh(agregat.economies.energie_wh_evitee)}</span>
              </div>
              <div className="eco-item">
                <span className="k">CO₂e évité ~</span>
                <span className="v num">{fmtCo2(agregat.economies.co2e_evite_g)}</span>
              </div>
            </div>
            <p className="eco-methode">{agregat.economies.methode}</p>
          </section>

          <section className="panel panel-pad">
            <div className="panel-h">
              <h2>Flux des appels</h2>
              <IndicateurFlux etat={etat} />
            </div>
            {etat === "polling" ? (
              <p className="flux-repli">
                Flux temps réel indisponible — repli en interrogation périodique de{" "}
                <code>/api/greenit</code>. Les totaux restent à jour, la liste
                d’appels ne se remplit pas.
              </p>
            ) : null}
            {flux.length === 0 ? (
              <p className="muted" style={{ fontSize: 13, margin: 0 }}>
                En attente d’un appel d’API… Le pipeline n’écrit dans le grand
                livre que pendant un run (diagnostic, découverte, export).
              </p>
            ) : (
              <div className="tablewrap" style={{ boxShadow: "none", border: "none" }}>
                <table
                  className="data flux-table"
                  aria-label="Derniers appels d’API journalisés, du plus récent au plus ancien"
                >
                  <thead>
                    <tr>
                      <th scope="col">Heure</th>
                      <th scope="col">Fournisseur</th>
                      <th scope="col">Modèle / profil</th>
                      <th scope="col" className="num">
                        Coût
                      </th>
                      <th scope="col" className="num">
                        Octets
                      </th>
                      <th scope="col" className="num">
                        Durée
                      </th>
                      <th scope="col" className="num">
                        CO₂e ~
                      </th>
                      <th scope="col">État</th>
                    </tr>
                  </thead>
                  <tbody aria-live="polite" aria-relevant="additions">
                    {flux.map((a, i) => (
                      <tr key={`${a.ts ?? ""}-${i}`} style={{ cursor: "default" }}>
                        <td className="mono">{fmtHeure(a.ts)}</td>
                        <td>
                          <div className="rowname mono">{a.fournisseur}</div>
                          <div className="rowsub mono">{a.endpoint}</div>
                        </td>
                        <td className="mono">
                          {a.modele ?? "—"}
                          {a.profil ? <span className="rowsub"> · {a.profil}</span> : null}
                        </td>
                        <td className="num">{fmtUsd(a.cout_estime, a.devise)}</td>
                        <td className="num">{fmtOctets(a.octets)}</td>
                        <td className="num">{fmtDuree(a.duree_ms)}</td>
                        <td className="num">{fmtCo2(a.co2e_g)}</td>
                        <td>
                          <span className={`pill ${classeResultat(a)}`}>
                            <span className="glyph" aria-hidden="true" />
                            {libelleResultat(a)}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <div className="grid grid-2">
            <PanneauBarres
              titre="Par modèle"
              sousTitre="coût cumulé"
              colonne="Modèle"
              lignes={agregat.par_modele.map((m) => ({ ...m, nom: m.modele }))}
            />
            <PanneauBarres
              titre="Par fournisseur"
              sousTitre="coût cumulé"
              colonne="Fournisseur"
              lignes={agregat.par_fournisseur.map((f) => ({ ...f, nom: f.fournisseur }))}
            />
          </div>

          {!agregat.ledger_present ? (
            <p className="muted" style={{ fontSize: 12.5 }}>
              Aucun grand livre trouvé à <code>{agregat.ledger_path}</code> — les
              totaux resteront à zéro tant qu’aucun run n’aura journalisé d’appel.
            </p>
          ) : null}
          {agregat.nb_lignes_illisibles > 0 ? (
            <p className="rgpd">
              {fmtInt(agregat.nb_lignes_illisibles)} ligne(s) illisible(s) ignorée(s)
              dans le grand livre.
            </p>
          ) : null}
        </>
      ) : null}
    </div>
  );
}
