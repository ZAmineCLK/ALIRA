# CLARA – Companion Libre Adaptatif de Réflexion Assisté

> Chatbot libre, non‑improvisateur, à apprentissage progressif **et ciblé**. Fonctionne sur machine modeste grâce à une base MySQL et un pipeline NLP léger.

## ✨ Principes

* **Libre & gratuit** : projet open source.
* **Pas d’improvisation** : si CLARA ne sait pas, elle le dit et demande une clarification.
* **Adaptatif** : apprentissage ciblé selon les intérêts de l’utilisateur + hiérarchie de contextes.
* **Économe en ressources** : connaissances externalisées (MySQL), petits modèles locaux.

## 🧠 Architecture (vue d’ensemble)

1. **Prétraitement linguistique** (correction, découpage, nettoyage) via `core/nlp_processor.py`.
2. **Raisonnement interne** (mémoire locale) via `MySQL'
3. **Escalade** vers **nounou** (assistant formateur) via `core/assistant_model.py` et `core/learning_system.py`.
4. **Fallback** Wikipédia si aucune connaissance (généraliste) via `core/wikipedia_fallback.py`.
5. **Stockage** : MySQL (synonymes par *familles*, contextes hiérarchiques, profils), cache mémoire.


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

## 🧩 Modèle sémantique

* **Familles de synonymes** dans un **seul champ** (zéro doublon).
* **Contextes hiérarchiques** (`contextes.parent_id`) et **index** mots↔contextes.
* **Désambiguïsation** par **comptage** des mots par contexte + **segmentation** (conjonctions). Les segments peuvent générer **deux réponses** si deux contextes séparés.
* **Protocole d’apprentissage des inconnus** : si un mot `Y` est inconnu, CLARA ne propose **aucune équivalence** ; elle demande une **définition** ou un **lien**. Après validation, mise à jour MySQL.

## 🚀 Installation rapide

```bash
# 1) Cloner
git clone https://github.com/<votre-compte>/clara.git
cd clara

# 2) Créer l’environnement
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3) Dépendances
pip install -r requirements.txt

# 4) Variables d’environnement (exemple)
export CLARA_DB_URL="mysql+pymysql://user:password@localhost:3306/clara"

# 5) Lancer
python -m clara.main
```

## 📦 Dépendances (exemple `requirements.txt`)

```
pymysql
sqlalchemy
wikipedia
python-dotenv
rapidfuzz
langdetect
```


## ⚙️ Config (exemple)

* `config/settings.py` : seuils de désambiguïsation, langues, flags “no‑improvise”.
* `config/database.py` : session/pooling MySQL, initialisation des tables.

## 🧪 Tests

* Tests unitaires sur : NLP, apprentissage, index contextes, MySQL manager.


## 📜 Licence

* Projet **libre**. : 
**GPL‑3.0** (garantit la liberté des dérivés)

## 🗺️ Roadmap (extrait)

* [ ] Implémentation familles de synonymes + index contextes
* [ ] Désambiguïsation segmentée (conjonctions)
* [ ] Protocole apprentissage des inconnus (Y inconnu)
* [ ] Nounou : interface d’annotation/validation
* [ ] Cache réponses + apprentissage différé
* [ ] Export/Import mémoire (dump MySQL)

## 🙌 Crédits & philosophie

CLARA est un **compagnon libre** : honnête (dit “je ne sais pas”),
adaptatif (apprentissage ciblé), et **économe** en ressources.

— Mainteneur : *ZAmineCLK* 💚
