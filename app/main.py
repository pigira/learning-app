"""Moteur FastAPI de l'application d'apprentissage.

Routes HTML (accueil, chapitre) + API JSON de progression.
Le moteur ne connaît rien du contenu : voir ``content.py``.

Lancement :  uvicorn app.main:app --reload
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

import markdown as md
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import content, database
from .models import Chapitre, ExerciceProgress, ProjetProgress

BASE_DIR = Path(__file__).resolve().parent

STATUT_LABELS = {
    "non_commence": "Non commencé",
    "en_cours": "En cours",
    "termine": "Terminé",
}


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    database.init_db()
    yield


app = FastAPI(title="Apprendre Python", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

templates = Jinja2Templates(directory=BASE_DIR / "templates")
templates.env.filters["markdown"] = lambda texte: md.markdown(
    texte, extensions=["fenced_code", "tables"]
)


def _statut_chapitre(chap: Chapitre, faits: set[str], projet_ok: bool) -> str:
    """Statut global : non_commence | en_cours | termine."""
    total = len(chap.exercices)
    exercices_ok = total > 0 and len(faits) == total
    if exercices_ok and (chap.projet is None or projet_ok):
        return "termine"
    if faits or projet_ok:
        return "en_cours"
    return "non_commence"


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    chapitres, erreurs = content.charger_chapitres()
    faits_par_chapitre = database.tous_exercices_faits()
    projets_ok = database.tous_projets_faits()

    cartes = []
    for chap in chapitres:
        ids = {e.id for e in chap.exercices}
        # Intersection : ignore d'éventuelles entrées orphelines en base
        # (exercice renommé ou supprimé du contenu).
        faits = faits_par_chapitre.get(chap.slug, set()) & ids
        projet_ok = chap.slug in projets_ok
        statut = _statut_chapitre(chap, faits, projet_ok)
        cartes.append(
            {
                "chap": chap,
                "nb_faits": len(faits),
                "nb_total": len(ids),
                "projet_ok": projet_ok,
                "statut": statut,
                "statut_label": STATUT_LABELS[statut],
            }
        )
    return templates.TemplateResponse(
        request, "index.html", {"cartes": cartes, "erreurs": erreurs}
    )


@app.get("/chapitre/{slug}", response_class=HTMLResponse)
async def page_chapitre(request: Request, slug: str) -> HTMLResponse:
    try:
        chap = content.obtenir_chapitre(slug)
    except content.ErreurContenu as exc:
        # Contenu présent mais invalide : erreur explicite pour l'auteur.
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    if chap is None:
        raise HTTPException(status_code=404, detail=f"Chapitre inconnu : {slug}")

    ids = {e.id for e in chap.exercices}
    faits = database.exercices_faits(slug) & ids
    projet_ok = database.projet_fait(slug)
    tous_faits = bool(ids) and faits == ids
    return templates.TemplateResponse(
        request,
        "chapitre.html",
        {
            "chap": chap,
            "faits": faits,
            "projet_ok": projet_ok,
            "tous_faits": tous_faits,
        },
    )


def _chapitre_ou_404(slug: str) -> Chapitre:
    try:
        chap = content.obtenir_chapitre(slug)
    except content.ErreurContenu as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    if chap is None:
        raise HTTPException(status_code=404, detail=f"Chapitre inconnu : {slug}")
    return chap


@app.post("/api/progress/exercice")
async def maj_exercice(payload: ExerciceProgress) -> dict:
    chap = _chapitre_ou_404(payload.chapitre)
    ids = {e.id for e in chap.exercices}
    if payload.exercice_id not in ids:
        raise HTTPException(
            status_code=404, detail=f"Exercice inconnu : {payload.exercice_id}"
        )
    database.set_exercice_fait(payload.chapitre, payload.exercice_id, payload.fait)
    faits = database.exercices_faits(payload.chapitre) & ids
    return {
        "ok": True,
        "faits": len(faits),
        "total": len(ids),
        "tous_faits": faits == ids,
    }


@app.post("/api/progress/projet")
async def maj_projet(payload: ProjetProgress) -> dict:
    chap = _chapitre_ou_404(payload.chapitre)
    if chap.projet is None:
        raise HTTPException(
            status_code=404, detail=f"Pas de projet pour : {payload.chapitre}"
        )
    database.set_projet_fait(payload.chapitre, payload.fait)
    return {"ok": True, "fait": payload.fait}
