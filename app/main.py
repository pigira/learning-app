"""Moteur FastAPI de l'application d'apprentissage.

Routes HTML (hub, cours, chapitre) + API JSON de progression.
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
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from . import content, database
from .models import Chapitre, CoursMeta, ExerciceProgress, ProjetProgress

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


app = FastAPI(title="Hub Apprentissage", lifespan=lifespan)

# Derrière le reverse proxy d'Azure App Service (TLS terminé en amont, requête
# transmise en HTTP interne), Starlette construit ses URLs absolues (url_for,
# request.base_url) à partir du schéma de la connexion reçue : http. Ce
# middleware lit le header X-Forwarded-Proto ajouté par le proxy Azure et
# corrige le scope ASGI en conséquence, pour que les URLs générées restent en
# https. Sans lui, le CSS/JS servis via url_for('static', ...) pointent vers
# http:// et sont bloqués par le navigateur (contenu mixte sur page https).
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

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


def _cartes_chapitres(cours_slug: str, chapitres: list[Chapitre]) -> list[dict]:
    """Assemble les statuts partagés entre le hub et la page du cours."""
    faits_par_chapitre = database.tous_exercices_faits(cours_slug)
    projets_ok = database.tous_projets_faits(cours_slug)

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
    return cartes


def _cours_meta_ou_404(cours_slug: str) -> CoursMeta:
    try:
        meta = content.obtenir_cours_meta(cours_slug)
    except content.ErreurContenu as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    if meta is None:
        raise HTTPException(status_code=404, detail=f"Cours inconnu : {cours_slug}")
    return meta


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    cours, erreurs = content.charger_cours()
    cartes = []
    for un_cours in cours:
        chapitres = (
            _cartes_chapitres(un_cours.slug, un_cours.chapitres)
            if un_cours.meta.statut == "disponible"
            else []
        )
        cartes.append(
            {
                "cours": un_cours,
                "nb_termines": sum(c["statut"] == "termine" for c in chapitres),
                "nb_total": len(un_cours.chapitres),
                "a_progression": any(c["statut"] != "non_commence" for c in chapitres),
            }
        )
    return templates.TemplateResponse(
        request, "hub.html", {"cartes": cartes, "erreurs": erreurs}
    )


@app.get("/cours/{cours_slug}", response_class=HTMLResponse)
async def page_cours(request: Request, cours_slug: str) -> HTMLResponse:
    cours_meta = _cours_meta_ou_404(cours_slug)
    chapitres, erreurs = content.charger_chapitres(cours_slug)
    return templates.TemplateResponse(
        request,
        "cours.html",
        {
            "cours_slug": cours_slug,
            "cours_meta": cours_meta,
            "cartes": _cartes_chapitres(cours_slug, chapitres),
            "erreurs": erreurs,
        },
    )


@app.get("/cours/{cours_slug}/chapitre/{slug}", response_class=HTMLResponse)
async def page_chapitre(request: Request, cours_slug: str, slug: str) -> HTMLResponse:
    cours_meta = _cours_meta_ou_404(cours_slug)
    chap = _chapitre_ou_404(cours_slug, slug)

    ids = {e.id for e in chap.exercices}
    faits = database.exercices_faits(cours_slug, slug) & ids
    projet_ok = database.projet_fait(cours_slug, slug)
    tous_faits = bool(ids) and faits == ids
    return templates.TemplateResponse(
        request,
        "chapitre.html",
        {
            "cours_slug": cours_slug,
            "cours_meta": cours_meta,
            "chap": chap,
            "faits": faits,
            "projet_ok": projet_ok,
            "tous_faits": tous_faits,
        },
    )


def _chapitre_ou_404(cours_slug: str, slug: str) -> Chapitre:
    try:
        chap = content.obtenir_chapitre(cours_slug, slug)
    except content.ErreurContenu as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    if chap is None:
        raise HTTPException(status_code=404, detail=f"Chapitre inconnu : {slug}")
    return chap


@app.post("/api/progress/exercice")
async def maj_exercice(payload: ExerciceProgress) -> dict:
    chap = _chapitre_ou_404(payload.cours, payload.chapitre)
    ids = {e.id for e in chap.exercices}
    if payload.exercice_id not in ids:
        raise HTTPException(
            status_code=404, detail=f"Exercice inconnu : {payload.exercice_id}"
        )
    database.set_exercice_fait(
        payload.cours, payload.chapitre, payload.exercice_id, payload.fait
    )
    faits = database.exercices_faits(payload.cours, payload.chapitre) & ids
    return {
        "ok": True,
        "faits": len(faits),
        "total": len(ids),
        "tous_faits": faits == ids,
    }


@app.post("/api/progress/projet")
async def maj_projet(payload: ProjetProgress) -> dict:
    chap = _chapitre_ou_404(payload.cours, payload.chapitre)
    if chap.projet is None:
        raise HTTPException(
            status_code=404, detail=f"Pas de projet pour : {payload.chapitre}"
        )
    database.set_projet_fait(payload.cours, payload.chapitre, payload.fait)
    return {"ok": True, "fait": payload.fait}
