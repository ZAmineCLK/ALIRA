---

# ALIRA – Accompagnante Libre à Interaction et Réflexion Assistée

*Née de la mythologie, forgée par la technologie*

---

## Concept

ALIRA est un système d’accompagnement intelligent et modulaire, conçu pour interagir avec l’utilisateur de manière claire et précise. Son objectif est de fournir des réponses fiables et contextualisées, tout en respectant sa philosophie fondamentale : **si ALIRA ne sait pas, elle dit qu’elle ne sait pas**.

---

## Nom et identité

Le nom **ALIRA** reflète la double nature du projet :

### Acronyme technique

**Accompagnante Libre à Interaction et Réflexion Assistée**
Signifie la capacité d’ALIRA à guider, interagir et réfléchir avec l’utilisateur de manière autonome, tout en restant ouverte et adaptable.

### Dimension symbolique et phonétique

La sonorité féminine **-a** évoque un nom de déesse moderne, inspiré de la mythologie grecque, conférant une aura de sagesse, guidance et intuition.

---

## Philosophie

* **Honnêteté** : ALIRA ne devine pas, elle ne comble pas les lacunes par improvisation.
* **Contextualisation** : elle utilise un système hiérarchique de contextes pour fournir des réponses cohérentes et pertinentes.
* **Adaptabilité** : capable d’apprendre des mots inconnus et d’enrichir sa mémoire de manière sécurisée et structurée.

---

## 🧠 Architecture (vue d’ensemble)

* **Prétraitement linguistique** : correction, découpage, nettoyage via `core/nlp_processor.py`.
* **Raisonnement interne (mémoire locale)** : gestion via MySQL.
* **Escalade vers “nounou”** (assistant formateur) via `core/assistant_model.py` et `core/learning_system.py`.
* **Fallback Wikipédia** si aucune connaissance (généraliste) via `core/wikipedia_fallback.py`.
* **Stockage** : MySQL (synonymes par familles, contextes hiérarchiques, profils), cache mémoire.

---

## 🔗 Flux décisionnel (simplifié)

```
Input utilisateur → NLP (préparation) → Connaissances locales ?
   ├─ Oui → Réponse → Fin
   └─ Non → Nounou sait ?
         ├─ Oui → Apprentissage + Réponse
         └─ Non → Wikipédia (généraliste) ?
               ├─ Oui → Réponse + (optionnel) apprentissage différé
               └─ Non → “Je ne sais pas, peux-tu préciser ?”
```

---

## 🧩 Modèle sémantique

* Familles de synonymes dans un seul champ (zéro doublon).
* Contextes hiérarchiques (`contextes.parent_id`) et index mots ↔ contextes.
* Désambiguïsation par comptage des mots par contexte + segmentation (conjonctions).
  Les segments peuvent générer deux réponses si deux contextes séparés.
* **Protocole d’apprentissage des inconnus** : si un mot est inconnu, ALIRA ne propose aucune équivalence ; elle demande une définition ou un lien. Après validation, mise à jour MySQL.

---

## 📦 Dépendances

Exemple `requirements.txt` :

```
pymysql
sqlalchemy
wikipedia
python-dotenv
rapidfuzz
langdetect
```

---

## ⚙️ Configuration

* `config/settings.py` : seuils de désambiguïsation, langues, flags “no‑improvise”.
* `config/database.py` : session/pooling MySQL, initialisation des tables.

---

## 🧪 Tests

Tests unitaires sur : NLP, apprentissage, index contextes, MySQL manager.

---

## 📜 Licence

Projet libre : **GPL‑3.0** (garantit la liberté des dérivés).

---

## 🙌 Crédits & philosophie

ALIRA est une **compagnante libre** :

* **Honnête** : dit “je ne sais pas” si nécessaire.
* **Adaptative** : apprentissage ciblé et sécurisé.
* **Économe en ressources** : fonctionne sur des machines modestes.

**Mainteneur** : ZAmineCLK 💚

---
