// AsyncState.tsx — enveloppe d'affichage des états loading / error / vide.

import type { ReactNode } from "react";

export function Loading({ label = "Chargement…" }: { label?: string }) {
  return (
    <div className="state-box" role="status" aria-live="polite">
      {label}
    </div>
  );
}

export function ErrorBox({ message }: { message: string }) {
  return (
    <div className="state-box err" role="alert">
      Erreur : {message}
    </div>
  );
}

export function EmptyBox({ label }: { label: string }) {
  return <div className="state-box">{label}</div>;
}

interface AsyncViewProps<T> {
  state: { data: T | null; loading: boolean; error: string | null };
  children: (data: T) => ReactNode;
  loadingLabel?: string;
}

// Rendu conditionnel selon l'état async : garde les vues courtes.
export function AsyncView<T>({ state, children, loadingLabel }: AsyncViewProps<T>) {
  if (state.loading) return <Loading label={loadingLabel} />;
  if (state.error) return <ErrorBox message={state.error} />;
  if (state.data == null) return <EmptyBox label="Aucune donnée." />;
  return <>{children(state.data)}</>;
}
