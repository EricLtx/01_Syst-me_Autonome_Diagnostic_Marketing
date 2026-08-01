// Preflight.tsx — liste des contrôles GO/NO-GO avec niveau (bloquant/warn) et
// pastille ok/ko, verdict global. L'état se lit à la rayure de sévérité.

import { api } from "../api";
import { useAsync } from "../hooks/useAsync";
import { AsyncView } from "../components/AsyncState";
import { VerdictBanner } from "../components/VerdictBanner";

export function Preflight() {
  const state = useAsync(() => api.preflight(), []);

  return (
    <div className="stack">
      <div className="page-head">
        <span className="eyebrow">Mise en route</span>
        <h1>Préflight GO / NO-GO</h1>
        <p>
          Contrôles bloquants et avertissements avant tout run réel. Pré-condition
          du cron d'orchestration. Un seul bloquant en échec = NO-GO.
        </p>
      </div>

      <AsyncView state={state} loadingLabel="Exécution des contrôles…">
        {(pf) => {
          const bloquants = pf.checks.filter((c) => c.niveau === "bloquant");
          const warns = pf.checks.filter((c) => c.niveau === "warn");
          return (
            <>
              <VerdictBanner preflight={pf} />

              <section className="stack" style={{ gap: 10 }}>
                <div className="panel-h">
                  <h2 style={{ fontSize: 14 }}>
                    Bloquants
                    <span className="muted mono" style={{ fontWeight: 400, marginLeft: 8 }}>
                      {bloquants.filter((c) => c.ok).length}/{bloquants.length} OK
                    </span>
                  </h2>
                </div>
                {bloquants.map((c, idx) => (
                  <CheckRow key={`${c.nom}-${idx}`} check={c} />
                ))}
              </section>

              {warns.length > 0 ? (
                <section className="stack" style={{ gap: 10 }}>
                  <div className="panel-h">
                    <h2 style={{ fontSize: 14 }}>
                      Avertissements
                      <span className="muted mono" style={{ fontWeight: 400, marginLeft: 8 }}>
                        non bloquants
                      </span>
                    </h2>
                  </div>
                  {warns.map((c, idx) => (
                    <CheckRow key={`${c.nom}-w-${idx}`} check={c} />
                  ))}
                </section>
              ) : null}
            </>
          );
        }}
      </AsyncView>
    </div>
  );
}

function CheckRow({
  check,
}: {
  check: { nom: string; niveau: "bloquant" | "warn"; ok: boolean; message: string };
}) {
  const cls = check.ok ? "ok" : `ko ${check.niveau}`;
  return (
    <div className={`check ${cls}`}>
      <div className="stripe" aria-hidden="true" />
      <div className="body">
        <div className="top">
          <span className="nom">{check.nom}</span>
          <span className={`lvl ${check.niveau}`}>{check.niveau}</span>
        </div>
        <div className="msg">{check.message}</div>
      </div>
      <div className="state" aria-label={check.ok ? "réussi" : "échec"}>
        {check.ok ? "✓ OK" : "✕ KO"}
      </div>
    </div>
  );
}
