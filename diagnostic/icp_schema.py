"""
icp_schema.py — validation des fichiers ICP (Ideal Customer Profile).

Un ICP est un fichier YAML dans icp/*.yaml. Ce module valide sa structure
exactement comme vault_schema.py valide les fiches prospect :
  - IcpConfig  : le profil complet (gabarits, localités, filtres, enrichissement)
  - Candidate  : entreprise découverte par SERP, en mémoire uniquement (jamais persistée ici)

Règle clé : icp_id = "persona{persona}-{marche}" — toujours cohérent.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class Requetes(BaseModel):
    model_config = ConfigDict(extra="forbid")

    gabarits: list[str]
    localites: list[str]
    max_resultats_par_requete: int = 10

    @field_validator("gabarits")
    @classmethod
    def gabarits_ont_localite(cls, v: list[str]) -> list[str]:
        for g in v:
            if "{localite}" not in g:
                raise ValueError(f"Gabarit sans {{localite}} : {g!r}")
        return v


class Filtres(BaseModel):
    model_config = ConfigDict(extra="forbid")

    domaines_exclus: list[str] = []
    exiger_domaine_propre: bool = True


class Enrichissement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    titres_cibles: list[str]
    max_enrichissements: int = 25


class IcpConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    icp_id: str
    persona: int
    marche: str
    description: str
    requetes: Requetes
    filtres: Filtres
    enrichissement: Enrichissement

    @model_validator(mode="after")
    def icp_id_coherent(self) -> "IcpConfig":
        attendu = f"persona{self.persona}-{self.marche}"
        if self.icp_id != attendu:
            raise ValueError(
                f"icp_id {self.icp_id!r} incohérent avec persona={self.persona} "
                f"et marche={self.marche!r} (attendu : {attendu!r})"
            )
        return self

    def generer_requetes(self) -> list[str]:
        """Produit cartésien gabarits × localités → requêtes SERP prêtes à l'envoi."""
        return [
            g.format(localite=loc)
            for g in self.requetes.gabarits
            for loc in self.requetes.localites
        ]


class Candidate(BaseModel):
    """Entreprise découverte par SERP. Objet en mémoire uniquement.

    Mappée vers FicheProspect (statut=decouvert) par run_discovery.py
    avant persistance dans le vault via vault_io.write_fiche().
    """

    model_config = ConfigDict(extra="forbid")

    nom: str
    site_web: str
    icp_id: str
    source: str            # ex. "serp:installateur thermopompe Québec"
    date_decouverte: date
