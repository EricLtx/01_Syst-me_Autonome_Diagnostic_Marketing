"""
faux_api.py — serveur d'API local pour les tests d'intégration bout-en-bout.

POURQUOI un vrai serveur HTTP plutôt que des mocks Python : on veut exercer le
VRAI chemin réseau du système — `api_io.call()`, son cache disque, ses budgets,
son grand livre — pas le court-circuiter. Les collecteurs font de vrais
`requests.get/post`, le SDK Anthropic fait un vrai POST HTTP ; seule la
destination change (`*_BASE_URL` → ce serveur au lieu de la production).

Zéro dépendance : `http.server` de la stdlib. TLS optionnel via le binaire
`openssl` (certificat auto-signé couvrant 127.0.0.1 → 127.0.0.9).

Endpoints émulés
----------------
  GET  /search                              → SerpAPI (résultats organiques)
  POST /v1/people/search                    → Apollo (personnes + email_status)
  GET  /maps/api/place/textsearch/json      → Google Places (text search)
  GET  /maps/api/place/details/json         → Google Places (details + avis)
  POST /v1/messages                         → API Messages Anthropic (format exact)
  GET  /sites/<slug>                        → site web d'un installateur HVAC
  GET  /sitemap.xml                         → sitemap (site « correct » seulement)
  GET  /__journal                            → journal des requêtes reçues (JSON)
  GET  /__sante                              → sonde de vie

Pourquoi les liens SERP pointent sur des IP de bouclage (127.0.0.2, 127.0.0.3…)
et non sur de vrais domaines : `discovery._normaliser_url()` force le schéma
https et déduplique par domaine. Une IP de bouclage distincte par entreprise
donne donc (a) une clé de dédup réaliste, (b) un site réellement joignable en
https par le diagnostic — le tout sans jamais sortir de la machine. Les
résultats à exclure (pagesjaunes.ca, facebook.com, wixsite.com) gardent leurs
vrais domaines : ils sont filtrés par l'ICP et ne sont jamais fetchés.
"""

from __future__ import annotations

import json
import re
import shutil
import ssl
import subprocess
import tempfile
import threading
import zlib
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from datetime import time as dtime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

# ---------------------------------------------------------------------------
# Catalogue d'entreprises fictives (persona 1 — HVAC Québec)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Entreprise:
    """Une entreprise fictive, cohérente d'un endpoint à l'autre.

    Le même slug pilote le site web, la fiche Places, les avis et les
    personnes Apollo : un test peut donc suivre une entreprise de bout en bout.
    """

    slug: str
    nom: str
    titre_serp: str
    ville: str
    ip: str                      # IP de bouclage servant de « domaine » unique
    qualite: str                 # "pauvre" | "correcte"
    rating: float | None
    nb_avis: int
    personnes: tuple[dict, ...]  # réponses Apollo brutes (champs en trop volontaires)
    # ADR 0004 (axe intention) : recrutement affiché sur la page d'accueil +
    # page carrières datée. Défaut False/12 : n'affecte AUCUNE entreprise
    # existante (HTML byte-identique quand recrute=False, cf. html_site()).
    recrute: bool = False
    jours_offre: int = 12


# 9 entreprises : 5 « pauvres » (beaucoup de failles → matière à diagnostic),
# 2 « correctes » (contre-exemple), 1 sans contact éligible chez Apollo,
# +1 « pauvre » recruteuse (ADR 0004, preuve de discrimination de l'axe
# intention à besoin égal).
CATALOGUE: tuple[Entreprise, ...] = (
    Entreprise(
        slug="climatisation-tremblay",
        nom="Climatisation Tremblay",
        titre_serp="Climatisation Tremblay | Installateur de thermopompes à Québec",
        ville="Québec",
        ip="127.0.0.2",
        qualite="pauvre",
        rating=3.4,
        nb_avis=7,
        personnes=(
            {
                "first_name": "Marc", "last_name": "Tremblay",
                "title": "Propriétaire",
                "email": "marc@climatisation-tremblay.test",
                "email_status": "verified",
                "linkedin_url": "https://www.linkedin.com/in/marc-tremblay-fictif",
                # Champs en trop : Contact(extra="forbid") doit les ignorer.
                "phone_numbers": ["+1-418-555-0101"], "city": "Québec",
                "organization": {"name": "Climatisation Tremblay", "employees": 12},
            },
            {
                "first_name": "Julie", "last_name": "Bergeron",
                "title": "Technicienne CVAC", "email": "julie@climatisation-tremblay.test",
                "email_status": "guessed",
            },
        ),
    ),
    Entreprise(
        slug="thermo-dufour",
        nom="Thermo Dufour",
        titre_serp="Thermo Dufour — Chauffage et climatisation à Lévis",
        ville="Lévis",
        ip="127.0.0.3",
        qualite="pauvre",
        rating=2.9,
        nb_avis=4,
        personnes=(
            {
                "first_name": "Sylvain", "last_name": "Dufour",
                "title": "Président", "email": "sylvain@thermo-dufour.test",
                "email_status": "verified",
                "linkedin_url": "https://www.linkedin.com/in/sylvain-dufour-fictif",
            },
        ),
    ),
    Entreprise(
        slug="cvac-gagnon-fils",
        nom="CVAC Gagnon et Fils",
        titre_serp="CVAC Gagnon et Fils · Thermopompe et chauffage — Trois-Rivières",
        ville="Trois-Rivières",
        ip="127.0.0.4",
        qualite="pauvre",
        rating=3.8,
        nb_avis=9,
        personnes=(
            {
                "first_name": "Nathalie", "last_name": "Gagnon",
                "title": "Propriétaire", "email": "n.gagnon@cvac-gagnon.test",
                "email_status": "likely",
            },
        ),
    ),
    Entreprise(
        slug="froid-boreal",
        nom="Froid Boréal",
        titre_serp="Froid Boréal - Climatisation résidentielle Sherbrooke",
        ville="Sherbrooke",
        ip="127.0.0.5",
        qualite="pauvre",
        rating=None,
        nb_avis=0,
        # Aucun titre ciblé : la candidate est écrite SANS contact (cas nominal
        # « fiche sans email » attendu par le rapport d'anomalies de l'export).
        personnes=(
            {"first_name": "Éric", "last_name": "Roy", "title": "Technicien senior",
             "email": "eric@froid-boreal.test", "email_status": "guessed"},
        ),
    ),
    Entreprise(
        slug="chauffage-lachance",
        nom="Chauffage Lachance",
        titre_serp="Chauffage Lachance | Entretien de fournaise à Laval",
        ville="Laval",
        ip="127.0.0.6",
        qualite="pauvre",
        rating=3.1,
        nb_avis=5,
        personnes=(
            {"first_name": "Pierre", "last_name": "Lachance", "title": "Owner",
             "email": "pierre@chauffage-lachance.test", "email_status": "verified"},
        ),
    ),
    Entreprise(
        slug="clim-rive-sud",
        nom="Clim Rive-Sud",
        titre_serp="Clim Rive-Sud — Thermopompes murales, Longueuil",
        ville="Longueuil",
        ip="127.0.0.7",
        qualite="correcte",
        rating=4.7,
        nb_avis=118,
        personnes=(
            {"first_name": "Karine", "last_name": "Meunier", "title": "Présidente",
             "email": "karine@clim-rive-sud.test", "email_status": "verified",
             "linkedin_url": "https://www.linkedin.com/in/karine-meunier-fictif"},
        ),
    ),
    Entreprise(
        slug="hvac-saguenay",
        nom="HVAC Saguenay",
        titre_serp="HVAC Saguenay : installation de thermopompe – Chicoutimi",
        ville="Chicoutimi",
        ip="127.0.0.8",
        qualite="correcte",
        rating=4.4,
        nb_avis=64,
        personnes=(
            {"first_name": "Alain", "last_name": "Simard", "title": "General Manager",
             "email": "alain@hvac-saguenay.test", "email_status": "verified"},
        ),
    ),
    Entreprise(
        slug="aeroclim-beauce",
        nom="Aéroclim Beauce",
        titre_serp="Aéroclim Beauce | Chauffagiste, Saint-Georges",
        ville="Saint-Georges",
        ip="127.0.0.9",
        qualite="pauvre",
        rating=3.6,
        nb_avis=12,
        personnes=(
            {"first_name": "Denis", "last_name": "Poulin", "title": "Directeur",
             "email": "denis@aeroclim-beauce.test", "email_status": "likely"},
        ),
    ),
    # ADR 0004 (axe intention) : entreprise « pauvre » en tous points
    # identique aux autres pour le BESOIN (même gabarit html_site()), mais
    # affichant un recrutement daté — la twin de contrôle pour la preuve de
    # discrimination est n'importe quelle autre entreprise "pauvre" ci-dessus
    # (recrute=False par défaut, HTML byte-identique à avant cette ADR).
    Entreprise(
        slug="thermo-marchand",
        nom="Thermo Marchand",
        titre_serp="Thermo Marchand | Chauffage et climatisation à Rimouski",
        ville="Rimouski",
        ip="127.0.0.10",
        qualite="pauvre",
        rating=3.2,
        nb_avis=6,
        personnes=(
            {"first_name": "Sophie", "last_name": "Marchand", "title": "Propriétaire",
             "email": "sophie@thermo-marchand.test", "email_status": "verified"},
        ),
        recrute=True,
        jours_offre=12,
    ),
)

PAR_SLUG: dict[str, Entreprise] = {e.slug: e for e in CATALOGUE}
PAR_IP: dict[str, Entreprise] = {e.ip: e for e in CATALOGUE}

# Résultats SERP toujours présents et toujours rejetés par les filtres ICP
# (domaines_exclus + exiger_domaine_propre). Ils prouvent que le filtre agit.
RESULTATS_A_EXCLURE: tuple[dict, ...] = (
    {"title": "Thermopompe à Québec | Pages Jaunes",
     "link": "https://www.pagesjaunes.ca/search/si/1/thermopompe/Quebec",
     "snippet": "Annuaire des installateurs de thermopompes."},
    {"title": "Clim Expert QC - Publications | Facebook",
     "link": "https://www.facebook.com/climexpertqc/",
     "snippet": "Page Facebook d'un installateur."},
    {"title": "Thermo Rive-Nord — Accueil",
     "link": "https://thermorivenord.wixsite.com/accueil",
     "snippet": "Site hébergé sur une plateforme mutualisée (pas de domaine propre)."},
)


# ---------------------------------------------------------------------------
# Génération des sites web (HTML réaliste)
# ---------------------------------------------------------------------------

def html_site(ent: Entreprise) -> str:
    """HTML du site d'une entreprise.

    « pauvre » : ni viewport, ni meta-description, ni logo, ni moyen de contact,
    copyright ancien, aucune image, ville accentuée uniquement (donc aucun
    mot-clé géolocalisé « quebec » détecté) → beaucoup de failles réelles.
    « correcte » : le contre-exemple complet.
    """
    if ent.qualite == "correcte":
        annee = date.today().year
        return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{ent.nom} — installation et entretien de thermopompe,
climatisation et chauffage à {ent.ville}, region de Quebec. Devis gratuit.">
<title>{ent.nom} — Thermopompe, climatisation et chauffage à {ent.ville}</title>
</head>
<body>
<header><img src="/static/logo-{ent.slug}.svg" alt="Logo {ent.nom}" class="logo"></header>
<h1>{ent.nom}</h1>
<p>Installation, entretien et reparation de thermopompe, climatisation,
ventilation et chauffage a {ent.ville} et partout dans la region de Quebec.</p>
<img src="/static/{ent.slug}-1.jpg" alt="Installation de thermopompe">
<img src="/static/{ent.slug}-2.jpg" alt="Unite de climatisation murale">
<img src="/static/{ent.slug}-3.jpg" alt="Entretien de fournaise">
<p>Telephone : <a href="tel:+14185550199">418 555-0199</a> —
<a href="mailto:info@{ent.slug}.test">info@{ent.slug}.test</a></p>
<p>Suivez-nous :
<a href="https://www.facebook.com/{ent.slug}">Facebook</a>
<a href="https://www.instagram.com/{ent.slug}">Instagram</a></p>
<time datetime="{date.today().isoformat()}">Derniere mise a jour</time>
<footer>© {annee} {ent.nom}. Tous droits reserves.</footer>
</body>
</html>
"""
    # ADR 0004 (axe intention) : ajout STRICTEMENT conditionnel — quand
    # `ent.recrute` est False (défaut, TOUTES les entreprises antérieures à
    # cette ADR), la ligne suivante est absente et le gabarit ci-dessous
    # produit un HTML byte-identique à avant cette ADR (aucune régression
    # possible sur les tests existants qui exercent ce gabarit).
    lignes = [
        "<html>",
        "<head>",
        f"<title>{ent.nom}</title>",
        "</head>",
        "<body>",
        f"<h1>{ent.nom}</h1>",
        f"<p>Installation de thermopompe, climatisation et chauffage à {ent.ville}.</p>",
        "<p>Nous desservons la région depuis 1998.</p>",
    ]
    if ent.recrute:
        lignes.append(
            f'<p><a href="/sites/{ent.slug}/carrieres">Carrières</a> : '
            "nous recrutons ! Rejoignez notre équipe, devenez installateur "
            "ou technicien CVAC.</p>"
        )
    lignes += [f"<p>© 2017 {ent.nom}</p>", "</body>", "</html>", ""]
    return "\n".join(lignes)


def html_carrieres(ent: Entreprise) -> str:
    """Page carrières d'une entreprise « recruteuse » (ADR 0004, Lot 2).

    Contient un <time> daté, extrait par
    `WebsiteCollector._try_page_carrieres()` lors de l'escalade (un seul
    appel de plus, déclenché uniquement si `offre_detectee` est vrai et
    qu'un lien carrières a été repéré sur la page d'accueil).
    """
    date_offre = (date.today() - timedelta(days=ent.jours_offre)).isoformat()
    return f"""<html>
<head><title>Carrières — {ent.nom}</title></head>
<body>
<h1>Carrières chez {ent.nom}</h1>
<p>Poste à pourvoir : installateur/technicien CVAC.</p>
<time datetime="{date_offre}">Offre publiée</time>
</body>
</html>
"""


def sitemap_site(ent: Entreprise) -> str | None:
    """Sitemap seulement pour les sites « corrects » (le reste renvoie 404)."""
    if ent.qualite != "correcte":
        return None
    recent = (date.today() - timedelta(days=9)).isoformat()
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"  <url><loc>/sites/{ent.slug}</loc><lastmod>{recent}</lastmod></url>\n"
        "</urlset>\n"
    )


# ---------------------------------------------------------------------------
# Fabriques de réponses par fournisseur
# ---------------------------------------------------------------------------

def reponse_serp(requete: str, num: int, port_https: int) -> dict:
    """Résultats organiques SerpAPI pour une requête.

    La fenêtre d'entreprises retournée dépend de la requête (décalage
    déterministe via crc32) et les fenêtres SE CHEVAUCHENT : deux requêtes
    différentes ramènent des entreprises communes, ce qui exerce réellement la
    déduplication intra-lot par domaine de `DiscoveryCollector`.
    """
    resultats: list[dict] = [dict(r) for r in RESULTATS_A_EXCLURE]
    n = len(CATALOGUE)
    depart = zlib.crc32(requete.encode("utf-8")) % n
    combien = max(1, min(num - len(resultats), n))
    for i in range(combien):
        ent = CATALOGUE[(depart + i) % n]
        resultats.append({
            "position": len(resultats) + 1,
            "title": ent.titre_serp,
            "link": f"https://{ent.ip}:{port_https}/sites/{ent.slug}",
            "displayed_link": f"{ent.ip}/sites/{ent.slug}",
            "snippet": f"{ent.nom} — installation et entretien de thermopompe "
                       f"à {ent.ville}.",
        })
    return {
        "search_metadata": {"id": f"faux-{zlib.crc32(requete.encode()):08x}",
                            "status": "Success"},
        "search_parameters": {"engine": "google", "q": requete, "google_domain": "google.ca"},
        "organic_results": resultats[:num] if num else resultats,
    }


def reponse_apollo(domaines: list[str], titres: list[str]) -> dict:
    """Réponse Apollo people/search pour un domaine d'entreprise.

    Le « domaine » vu par `enrichment.py` est le netloc du site_web, donc
    « 127.0.0.X:port » : on retrouve l'entreprise par son IP.
    """
    personnes: list[dict] = []
    for dom in domaines:
        hote = dom.split(":")[0]
        ent = PAR_IP.get(hote) or PAR_SLUG.get(hote)
        if ent is not None:
            personnes.extend(dict(p) for p in ent.personnes)
    return {
        "people": personnes,
        "pagination": {"page": 1, "per_page": 5, "total_entries": len(personnes)},
        "breadcrumbs": [{"label": "Titres", "values": titres}],
    }


def _trouver_par_texte(texte: str) -> Entreprise | None:
    """Retrouve une entreprise depuis un texte libre (query Places, prompt LLM)."""
    t = texte.lower()
    for ent in CATALOGUE:
        if ent.nom.lower() in t or ent.slug in t:
            return ent
    # Repli : premier mot significatif du nom (« Tremblay », « Dufour »…)
    for ent in CATALOGUE:
        distinctif = ent.nom.split()[-1].lower()
        if len(distinctif) > 3 and distinctif in t:
            return ent
    return None


def reponse_places_textsearch(query: str) -> dict:
    ent = _trouver_par_texte(query)
    if ent is None:
        return {"results": [], "status": "ZERO_RESULTS"}
    place: dict[str, Any] = {
        "name": ent.nom,
        "place_id": f"place_{ent.slug}",
        "business_status": "OPERATIONAL",
        "formatted_address": f"123 rue Principale, {ent.ville}, QC, Canada",
        "user_ratings_total": ent.nb_avis,
        "types": ["hvac_contractor", "point_of_interest", "establishment"],
    }
    if ent.rating is not None:
        place["rating"] = ent.rating
    if ent.qualite == "correcte":
        place["photos"] = [{"photo_reference": f"ref-{ent.slug}-{i}", "width": 1600}
                           for i in range(1, 4)]
    return {"results": [place], "status": "OK"}


def reponse_places_details(place_id: str) -> dict:
    ent = PAR_SLUG.get(place_id.removeprefix("place_"))
    if ent is None:
        return {"result": {}, "status": "NOT_FOUND"}
    # Horodatage epoch portable (pas de strftime("%s"), non standard).
    base_ts = int(datetime.combine(date.today() - timedelta(days=40),
                                   dtime(12, 0)).timestamp())
    avis: list[dict] = []
    for i in range(min(ent.nb_avis, 3)):
        a = {
            "author_name": f"Client {i + 1}",
            "rating": int(ent.rating or 3),
            "text": "Service correct, delais un peu longs.",
            "time": base_ts + i * 86400,
        }
        # Seules les entreprises « correctes » répondent aux avis.
        if ent.qualite == "correcte":
            a["owner_answer"] = "Merci pour votre commentaire !"
        avis.append(a)
    resultat: dict[str, Any] = {
        "name": ent.nom,
        "place_id": place_id,
        "user_ratings_total": ent.nb_avis,
        "reviews": avis,
    }
    if ent.rating is not None:
        resultat["rating"] = ent.rating
    return {"result": resultat, "status": "OK"}


_RE_PROSPECT = re.compile(r"prospect\s*:\s*(.+?)\s*\(", re.IGNORECASE)
_RE_FAILLE = re.compile(r"^-\s*\[(haute|moyenne|basse)\]\s*([^:]+):\s*(.+)$", re.MULTILINE)


def reponse_anthropic(corps: dict) -> dict:
    """Réponse au format EXACT de l'API Messages, dérivée du prompt reçu.

    Le faux modèle « rédige » à partir des seules failles présentes dans le
    prompt : la sortie passe donc le `quality_check` de synthesis.py (audit
    nominatif, adossé aux failles) sans jamais rien inventer — exactement ce
    qu'on attend du vrai modèle.
    """
    prompt = ""
    for msg in corps.get("messages") or []:
        contenu = msg.get("content")
        if isinstance(contenu, str):
            prompt += contenu
        elif isinstance(contenu, list):
            prompt += "".join(b.get("text", "") for b in contenu if isinstance(b, dict))

    m = _RE_PROSPECT.search(prompt)
    nom = m.group(1).strip() if m else "l'entreprise"
    failles = _RE_FAILLE.findall(prompt)

    lignes = [f"ACCROCHE: {failles[0][2]}" if failles
              else f"ACCROCHE: Presence digitale a consolider pour {nom}."]
    lignes += [
        "",
        f"# Mini-audit de marque — {nom}",
        "",
        f"Analyse factuelle de la presence digitale de {nom}, strictement adossee "
        "aux constats releves ci-dessous.",
        "",
        "## Points de friction",
    ]
    for gravite, dimension, preuve in failles[:5]:
        lignes.append(f"- **{dimension.strip()}** ({gravite}) : {preuve}")
    if not failles:
        lignes.append("- Aucun point bloquant sur les dimensions mesurees.")
    lignes += ["", "## Prochaine action", "Corriger d'abord le point le plus grave."]

    texte = "\n".join(lignes)
    return {
        "id": "msg_faux_" + f"{zlib.crc32(texte.encode()):08x}",
        "type": "message",
        "role": "assistant",
        "model": corps.get("model", "claude-sonnet-4-6"),
        "content": [{"type": "text", "text": texte}],
        "stop_reason": "end_turn",
        "stop_sequence": None,
        "usage": {
            # Approximation stable : 4 caractères ≈ 1 token.
            "input_tokens": max(1, len(prompt) // 4),
            "output_tokens": max(1, len(texte) // 4),
        },
    }


# ---------------------------------------------------------------------------
# Serveur
# ---------------------------------------------------------------------------

@dataclass
class RequeteRecue:
    """Une requête vue par le serveur — matière première des assertions."""
    methode: str
    chemin: str
    params: dict[str, list[str]] = field(default_factory=dict)
    corps: dict | None = None
    hote: str = ""
    tls: bool = False

    def to_dict(self) -> dict:
        return {"methode": self.methode, "chemin": self.chemin, "params": self.params,
                "corps": self.corps, "hote": self.hote, "tls": self.tls}


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "FauxApiLocal/1.0"

    # --- plomberie -------------------------------------------------------

    @property
    def faux(self) -> "ServeurFauxApi":
        return self.server.faux  # type: ignore[attr-defined]

    def log_message(self, *args) -> None:  # silence : le journal suffit
        pass

    def _envoyer_json(self, charge: dict, code: int = 200) -> None:
        data = json.dumps(charge, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _envoyer_texte(self, texte: str, code: int = 200,
                       mime: str = "text/html; charset=utf-8",
                       entetes: dict[str, str] | None = None) -> None:
        data = texte.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(data)))
        for k, v in (entetes or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def _lire_corps(self) -> dict | None:
        taille = int(self.headers.get("Content-Length") or 0)
        if not taille:
            return None
        brut = self.rfile.read(taille)
        try:
            return json.loads(brut.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return {"_brut": brut[:400].decode("utf-8", "replace")}

    def _tls(self) -> bool:
        return isinstance(self.connection, ssl.SSLSocket)

    # --- routage ---------------------------------------------------------

    def do_GET(self) -> None:  # noqa: N802 (nom imposé par BaseHTTPRequestHandler)
        parse = urlparse(self.path)
        params = parse_qs(parse.query)
        self.faux.enregistrer(RequeteRecue(
            "GET", parse.path, params, None, self.headers.get("Host", ""), self._tls()))
        self._router_get(parse.path, params)

    def do_POST(self) -> None:  # noqa: N802
        parse = urlparse(self.path)
        corps = self._lire_corps()
        self.faux.enregistrer(RequeteRecue(
            "POST", parse.path, parse_qs(parse.query), corps,
            self.headers.get("Host", ""), self._tls()))
        self._router_post(parse.path, corps or {})

    def _router_get(self, chemin: str, params: dict) -> None:
        if chemin == "/__sante":
            return self._envoyer_json({"ok": True, "service": "faux_api"})
        if chemin == "/__journal":
            return self._envoyer_json({"requetes": [r.to_dict() for r in self.faux.journal]})

        if chemin == "/search":
            requete = (params.get("q") or [""])[0]
            num = int((params.get("num") or ["10"])[0] or 10)
            return self._envoyer_json(
                reponse_serp(requete, num, self.faux.port_https or self.faux.port_http))

        if chemin == "/maps/api/place/textsearch/json":
            return self._envoyer_json(
                reponse_places_textsearch((params.get("query") or [""])[0]))

        if chemin == "/maps/api/place/details/json":
            return self._envoyer_json(
                reponse_places_details((params.get("place_id") or [""])[0]))

        if chemin == "/sitemap.xml":
            ent = PAR_IP.get(self.headers.get("Host", "").split(":")[0])
            xml = sitemap_site(ent) if ent else None
            if xml is None:
                return self._envoyer_json({"erreur": "sitemap absent"}, 404)
            return self._envoyer_texte(xml, mime="application/xml; charset=utf-8")

        if chemin.startswith("/sites/") and chemin.endswith("/carrieres"):
            # ADR 0004 (Lot 2) : page carrières — UNIQUEMENT pour une
            # entreprise « recruteuse » (recrute=True), 404 sinon (même
            # discipline que /sitemap.xml pour les sites non "correcte").
            slug = chemin[len("/sites/"):-len("/carrieres")].strip("/")
            ent = PAR_SLUG.get(slug)
            if ent is None or not ent.recrute:
                return self._envoyer_json({"erreur": f"page carrières inconnue : {slug}"}, 404)
            return self._envoyer_texte(html_carrieres(ent))

        if chemin.startswith("/sites/"):
            slug = chemin.removeprefix("/sites/").strip("/")
            ent = PAR_SLUG.get(slug)
            if ent is None:
                return self._envoyer_json({"erreur": f"site inconnu : {slug}"}, 404)
            entetes = {}
            if ent.qualite == "correcte":
                entetes["Last-Modified"] = "Mon, 08 Jul 2024 11:00:00 GMT"
            return self._envoyer_texte(html_site(ent), entetes=entetes)

        self._envoyer_json({"erreur": f"chemin inconnu : {chemin}"}, 404)

    def _router_post(self, chemin: str, corps: dict) -> None:
        if chemin == "/v1/people/search":
            return self._envoyer_json(reponse_apollo(
                list(corps.get("organization_domains") or []),
                list(corps.get("person_titles") or []),
            ))
        if chemin == "/v1/messages":
            return self._envoyer_json(reponse_anthropic(corps))
        self._envoyer_json({"erreur": f"chemin inconnu : {chemin}"}, 404)


class _Serveur(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def handle_error(self, request, client_address) -> None:
        # Un client qui parle en clair à un port TLS (ou l'inverse) lève ici :
        # c'est un cas de test légitime, pas une panne du serveur.
        pass


class ServeurFauxApi:
    """Serveur d'API local (HTTP + HTTPS optionnel) avec journal des requêtes.

    Écoute sur 0.0.0.0 : les alias de bouclage 127.0.0.2 … 127.0.0.9 servent de
    « domaines » distincts pour la déduplication de la découverte.
    """

    def __init__(
        self,
        *,
        tls: bool = True,
        hote: str = "0.0.0.0",
        port: int = 0,
        port_tls: int = 0,
    ) -> None:
        self._hote = hote
        self._tls_demande = tls
        self._port_demande = port
        self._port_tls_demande = port_tls
        self._journal: list[RequeteRecue] = []
        self._verrou = threading.Lock()
        self._http: _Serveur | None = None
        self._https: _Serveur | None = None
        self._threads: list[threading.Thread] = []
        self._dossier_cert: Path | None = None
        self.chemin_cert: Path | None = None

    # --- cycle de vie ----------------------------------------------------

    def demarrer(self) -> "ServeurFauxApi":
        self._http = _Serveur((self._hote, self._port_demande), _Handler)
        self._http.faux = self  # type: ignore[attr-defined]
        self._lancer(self._http)

        if self._tls_demande:
            cert = self._generer_certificat()
            if cert is not None:
                contexte = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                contexte.load_cert_chain(str(cert[0]), str(cert[1]))
                self._https = _Serveur((self._hote, self._port_tls_demande), _Handler)
                self._https.faux = self  # type: ignore[attr-defined]
                self._https.socket = contexte.wrap_socket(
                    self._https.socket, server_side=True)
                self._lancer(self._https)
        return self

    def _lancer(self, serveur: _Serveur) -> None:
        t = threading.Thread(target=serveur.serve_forever, daemon=True)
        t.start()
        self._threads.append(t)

    def arreter(self) -> None:
        for serveur in (self._http, self._https):
            if serveur is not None:
                serveur.shutdown()
                serveur.server_close()
        self._http = self._https = None
        if self._dossier_cert is not None:
            shutil.rmtree(self._dossier_cert, ignore_errors=True)
            self._dossier_cert = None

    def __enter__(self) -> "ServeurFauxApi":
        return self.demarrer()

    def __exit__(self, *exc) -> None:
        self.arreter()

    # --- certificat auto-signé (optionnel) -------------------------------

    def _generer_certificat(self) -> tuple[Path, Path] | None:
        """Certificat auto-signé couvrant 127.0.0.1 → 127.0.0.9.

        Repose sur le binaire `openssl` (présent partout où tourne le projet).
        Absent → le serveur reste en HTTP seul, sans faire échouer les tests.
        """
        if shutil.which("openssl") is None:
            return None
        dossier = Path(tempfile.mkdtemp(prefix="faux_api_tls_"))
        cert, cle = dossier / "cert.pem", dossier / "key.pem"
        ips = ",".join(f"IP:127.0.0.{i}" for i in range(1, 12))
        try:
            subprocess.run(
                ["openssl", "req", "-x509", "-newkey", "rsa:2048",
                 "-keyout", str(cle), "-out", str(cert), "-days", "30", "-nodes",
                 "-subj", "/CN=faux-api-local",
                 "-addext", f"subjectAltName={ips},DNS:localhost"],
                check=True, capture_output=True, timeout=60,
            )
        except (subprocess.SubprocessError, OSError):
            shutil.rmtree(dossier, ignore_errors=True)
            return None
        self._dossier_cert = dossier
        self.chemin_cert = cert
        return cert, cle

    # --- adresses --------------------------------------------------------

    @property
    def port_http(self) -> int:
        assert self._http is not None, "serveur non démarré"
        return self._http.server_address[1]

    @property
    def port_https(self) -> int:
        return self._https.server_address[1] if self._https is not None else 0

    @property
    def tls_actif(self) -> bool:
        return self._https is not None

    @property
    def base_http(self) -> str:
        return f"http://127.0.0.1:{self.port_http}"

    @property
    def base_https(self) -> str:
        if not self.tls_actif:
            raise RuntimeError("TLS non disponible sur ce serveur")
        return f"https://127.0.0.1:{self.port_https}"

    def url_site(self, slug: str, *, https: bool = False) -> str:
        """URL du site d'une entreprise du catalogue."""
        ent = PAR_SLUG[slug]
        if https:
            return f"https://{ent.ip}:{self.port_https}/sites/{slug}"
        return f"http://{ent.ip}:{self.port_http}/sites/{slug}"

    def variables_env(self) -> dict[str, str]:
        """Variables à poser pour rediriger TOUT le système vers ce serveur."""
        env = {
            "SERP_BASE_URL": self.base_http,
            "APOLLO_BASE_URL": self.base_http,
            "PLACES_BASE_URL": self.base_http,
            "ANTHROPIC_BASE_URL": self.base_http,
            # Clés factices : le faux serveur ne les vérifie pas, mais le code
            # (et le préflight) exige leur présence.
            "SERP_API_KEY": "faux-serp-cle-test",
            "APOLLO_API_KEY": "faux-apollo-cle-test",
            "GOOGLE_PLACES_API_KEY": "faux-places-cle-test",
            "ANTHROPIC_API_KEY": "faux-anthropic-cle-test",
        }
        if self.chemin_cert is not None:
            # requests fait confiance au certificat auto-signé du faux serveur.
            env["REQUESTS_CA_BUNDLE"] = str(self.chemin_cert)
        return env

    # --- journal ---------------------------------------------------------

    def enregistrer(self, requete: RequeteRecue) -> None:
        with self._verrou:
            self._journal.append(requete)

    @property
    def journal(self) -> list[RequeteRecue]:
        with self._verrou:
            return list(self._journal)

    def reinitialiser_journal(self) -> None:
        with self._verrou:
            self._journal.clear()

    def compter(self, chemin: str) -> int:
        """Nombre de requêtes reçues sur ce chemin exact."""
        return sum(1 for r in self.journal if r.chemin == chemin)

    def requetes(self, chemin: str) -> list[RequeteRecue]:
        return [r for r in self.journal if r.chemin == chemin]


def demarrer(*, tls: bool = True) -> ServeurFauxApi:
    """Raccourci : construit et démarre le serveur."""
    return ServeurFauxApi(tls=tls).demarrer()
