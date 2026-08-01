// markdown.tsx — rendu Markdown MAISON et SÛR : on parse un sous-ensemble et on
// produit des éléments React. Aucun dangerouslySetInnerHTML, aucune injection
// HTML possible (le texte devient des noeuds texte React, échappés par défaut).
//
// Sous-ensemble supporté : titres (#..###), listes à puces, citations (>),
// tableaux GFM (| a | b |), paragraphes, et inline **gras**, `code`, *italique*.

import type { ReactNode } from "react";

let keySeq = 0;
function k(): string {
  keySeq += 1;
  return `md-${keySeq}`;
}

// --- Inline : découpe une ligne en fragments (gras / code / italique / texte). ---
function renderInline(text: string): ReactNode[] {
  const nodes: ReactNode[] = [];
  // On traite `code` en premier (protège son contenu), puis **gras**, puis *italique*.
  const re = /(`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*)/g;
  let last = 0;
  let m: RegExpExecArray | null;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) nodes.push(text.slice(last, m.index));
    const tok = m[0];
    if (tok.startsWith("`")) {
      nodes.push(<code key={k()}>{tok.slice(1, -1)}</code>);
    } else if (tok.startsWith("**")) {
      nodes.push(<strong key={k()}>{tok.slice(2, -2)}</strong>);
    } else {
      nodes.push(<em key={k()}>{tok.slice(1, -1)}</em>);
    }
    last = m.index + tok.length;
  }
  if (last < text.length) nodes.push(text.slice(last));
  return nodes;
}

function isTableSeparator(line: string): boolean {
  return /^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)+\|?\s*$/.test(line);
}

function splitRow(line: string): string[] {
  return line
    .trim()
    .replace(/^\|/, "")
    .replace(/\|$/, "")
    .split("|")
    .map((c) => c.trim());
}

export function renderMarkdown(src: string): ReactNode {
  keySeq = 0;
  const lines = src.replace(/\r\n/g, "\n").split("\n");
  const out: ReactNode[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    // Ligne vide -> saut.
    if (line.trim() === "") {
      i += 1;
      continue;
    }

    // Titres.
    const h = /^(#{1,3})\s+(.*)$/.exec(line);
    if (h) {
      const level = h[1].length;
      const content = renderInline(h[2]);
      if (level === 1) out.push(<h1 key={k()}>{content}</h1>);
      else if (level === 2) out.push(<h2 key={k()}>{content}</h2>);
      else out.push(<h3 key={k()}>{content}</h3>);
      i += 1;
      continue;
    }

    // Tableau GFM : ligne d'en-tête suivie d'une ligne séparatrice.
    if (
      line.includes("|") &&
      i + 1 < lines.length &&
      isTableSeparator(lines[i + 1])
    ) {
      const header = splitRow(line);
      const rows: string[][] = [];
      i += 2;
      while (i < lines.length && lines[i].includes("|") && lines[i].trim() !== "") {
        rows.push(splitRow(lines[i]));
        i += 1;
      }
      out.push(
        <div className="md-tablewrap" key={k()}>
          <table>
            <thead>
              <tr>
                {header.map((c) => (
                  <th key={k()}>{renderInline(c)}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={k()}>
                  {r.map((c) => (
                    <td key={k()}>{renderInline(c)}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>,
      );
      continue;
    }

    // Citation (une ou plusieurs lignes >).
    if (/^\s*>\s?/.test(line)) {
      const buf: string[] = [];
      while (i < lines.length && /^\s*>\s?/.test(lines[i])) {
        buf.push(lines[i].replace(/^\s*>\s?/, ""));
        i += 1;
      }
      out.push(
        <blockquote key={k()}>{renderInline(buf.join(" "))}</blockquote>,
      );
      continue;
    }

    // Liste à puces (- ou *).
    if (/^\s*[-*]\s+/.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^\s*[-*]\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^\s*[-*]\s+/, ""));
        i += 1;
      }
      out.push(
        <ul key={k()}>
          {items.map((it) => (
            <li key={k()}>{renderInline(it)}</li>
          ))}
        </ul>,
      );
      continue;
    }

    // Paragraphe : agrège les lignes contiguës non-spéciales.
    const para: string[] = [];
    while (
      i < lines.length &&
      lines[i].trim() !== "" &&
      !/^(#{1,3})\s/.test(lines[i]) &&
      !/^\s*[-*]\s+/.test(lines[i]) &&
      !/^\s*>\s?/.test(lines[i]) &&
      !(lines[i].includes("|") && i + 1 < lines.length && isTableSeparator(lines[i + 1]))
    ) {
      para.push(lines[i]);
      i += 1;
    }
    out.push(<p key={k()}>{renderInline(para.join(" "))}</p>);
  }

  return <div className="md">{out}</div>;
}
