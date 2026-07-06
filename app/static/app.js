"use strict";

/* Apprendre Python — interactions côté client.
 * Aucune dépendance, aucun build. Trois responsabilités :
 *   1. révélation progressive des indices,
 *   2. affichage/masquage des corrections,
 *   3. enregistrement de la progression (checkboxes) via l'API.
 */

// ---------------------------------------------------------------------------
// 1. Indices progressifs : chaque groupe .indices débloque ses boutons un à un
// ---------------------------------------------------------------------------
document.querySelectorAll(".indices").forEach((groupe) => {
  const boutons = Array.from(groupe.querySelectorAll("button[data-role='indice']"));
  boutons.forEach((btn, i) => {
    btn.addEventListener("click", () => {
      const cible = document.getElementById(btn.dataset.cible);
      if (cible) cible.classList.remove("cache");
      btn.disabled = true;
      btn.classList.add("vu");
      if (boutons[i + 1]) boutons[i + 1].disabled = false;
    });
  });
});

// ---------------------------------------------------------------------------
// 2. Corrections : simple bascule affiché/masqué
// ---------------------------------------------------------------------------
document.querySelectorAll("button[data-role='solution']").forEach((btn) => {
  btn.addEventListener("click", () => {
    const cible = document.getElementById(btn.dataset.cible);
    if (!cible) return;
    const masque = cible.classList.toggle("cache");
    btn.textContent = masque ? "Voir la correction" : "Masquer la correction";
  });
});

// ---------------------------------------------------------------------------
// 3. Progression (uniquement sur les pages chapitre)
// ---------------------------------------------------------------------------
const slug = document.body.dataset.chapitre;

async function envoyer(url, payload) {
  const reponse = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!reponse.ok) throw new Error(`HTTP ${reponse.status}`);
  return reponse.json();
}

function majCompteur(faits, total) {
  const el = document.getElementById("compteur-exercices");
  if (el) el.textContent = `${faits}/${total}`;
}

function majVerrouProjet(tousFaits) {
  const verrou = document.getElementById("projet-verrou");
  const contenu = document.getElementById("projet-contenu");
  if (!verrou || !contenu) return;
  verrou.classList.toggle("cache", tousFaits);
  contenu.classList.toggle("cache", !tousFaits);
}

if (slug) {
  document.querySelectorAll("input[data-role='fait-exercice']").forEach((cb) => {
    cb.addEventListener("change", async () => {
      try {
        const data = await envoyer("/api/progress/exercice", {
          chapitre: slug,
          exercice_id: cb.dataset.exerciceId,
          fait: cb.checked,
        });
        majCompteur(data.faits, data.total);
        majVerrouProjet(data.tous_faits);
      } catch (err) {
        cb.checked = !cb.checked; // rétablit l'état affiché
        alert(`Enregistrement impossible (${err.message}). Le serveur tourne-t-il ?`);
      }
    });
  });

  const cbProjet = document.querySelector("input[data-role='fait-projet']");
  if (cbProjet) {
    cbProjet.addEventListener("change", async () => {
      try {
        await envoyer("/api/progress/projet", { chapitre: slug, fait: cbProjet.checked });
      } catch (err) {
        cbProjet.checked = !cbProjet.checked;
        alert(`Enregistrement impossible (${err.message}). Le serveur tourne-t-il ?`);
      }
    });
  }
}
