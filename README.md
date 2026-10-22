# Besoins en équipements publics à l'horizon 2050

Web app qui part d'un **ratio futur** choisi par l'utilisateur et en déduit le besoin brut, puis la
répartition entre annexes, SBP de bâtiments et emprise au sol (chemin inverse de la situation de
référence). Elle suit le fichier Excel `Tableau_SBP_SS - CD 22_10_26`.

Deux réglages, équipement par équipement :

- le **ratio futur** (m² équiv. SBP par habitant), par curseur (variation en %) ou saisie directe ;
- le **nombre de niveaux** des bâtiments, qui répartit la SBP entre sol et hauteur.

L'application a trois onglets :

1. **Par équipement** : un menu déroulant pour choisir l'équipement, puis trois blocs : la situation de
   référence (ratio actuel × population future = besoin brut), l'ajustement du ratio (besoin brut de
   la variante, variation, cercles proportionnels aux besoins), et la répartition du besoin (SBP
   bâtiments, annexes, emprise bâtie, sol total, niveaux du bâtiment, écarts).
2. **Vue d'ensemble** : tous les équipements, totaux par classe, exports Excel/CSV.
3. **Données et méthode**.

## Structure

```
equipements-app/
├── app.py                 # interface Streamlit
├── calculs.py             # modèle de calcul (indépendant de l'interface)
├── assets/
│   └── logo_6t.png        # sigle 6t (tiré du modèle PowerPoint 2023)
├── data/
│   └── equipements.csv    # données de référence et bornes
├── tests/
│   └── test_calculs.py    # vérifie que le modèle reproduit le fichier Excel
├── .streamlit/
│   └── config.toml        # thème de l'application
├── requirements.txt
└── .gitignore
```

## Installation dans VS Code

Prérequis : Python 3.10 ou plus récent, et l'extension Python de VS Code.

1. Ouvrir le dossier `equipements-app` dans VS Code (Fichier › Ouvrir le dossier).
2. Ouvrir un terminal (Terminal › Nouveau terminal) et créer un environnement virtuel :

   ```bash
   python -m venv .venv
   ```

3. Activer l'environnement :

   ```bash
   # Windows (PowerShell)
   .venv\Scripts\Activate.ps1
   # macOS / Linux
   source .venv/bin/activate
   ```

   Si VS Code propose d'utiliser cet environnement pour l'espace de travail, accepter.

4. Installer les dépendances :

   ```bash
   pip install -r requirements.txt
   ```

5. Lancer l'application :

   ```bash
   streamlit run app.py
   ```

   Elle s'ouvre dans le navigateur à l'adresse http://localhost:8501. Chaque enregistrement
   d'un fichier recharge l'application.

## Exporter les résultats

Dans l'onglet **Vue d'ensemble**, les boutons de téléchargement permettent d'obtenir
les résultats en Excel ou en CSV. Le bouton **Enregistrer sur disque** conserve les deux
fichiers dans le dossier `outputs/` à la racine du projet, à côté de `app.py`. Ce dossier est
ignoré par Git afin que les exports locaux ne soient pas ajoutés au dépôt.

## Vérifier les calculs

```bash
pytest
```

Les tests contrôlent que le modèle Python donne les mêmes résultats que le fichier Excel
(par exemple 1 196,4 ha équiv. SBP de besoin brut pour la référence future, et l'école primaire
à ratio 42 avec 4 niveaux : emprise bâtie de 206 505 m²).

## Modifier les données

Toutes les données sont dans `data/equipements.csv` : population actuelle et future de référence,
emprise des bâtiments, annexes (espaces extérieurs), niveaux actuels, et le niveau maximum. Le fichier s'ouvre dans Excel ou dans VS Code.

Garder le séparateur virgule et le point décimal, et ne pas renommer les colonnes.
Après modification, relancer `pytest` : les tests échoueront volontairement si les résultats de
référence changent. Mettre alors à jour les valeurs attendues dans `tests/test_calculs.py`.

## Publier sur GitHub

1. Créer un dépôt vide sur GitHub (sans README), par exemple `equipements-app`.
2. Dans le terminal de VS Code, à la racine du dossier :

   ```bash
   git init
   git add .
   git commit -m "Première version de l'application"
   git branch -M main
   git remote add origin https://github.com/<votre-compte>/equipements-app.git
   git push -u origin main
   ```

   On peut aussi passer par l'onglet Contrôle de code source de VS Code (« Publier sur GitHub »).

## Mettre l'application en ligne (facultatif)

Streamlit Community Cloud héberge gratuitement les applications à partir d'un dépôt GitHub :

1. Se connecter sur https://share.streamlit.io avec son compte GitHub.
2. Choisir « Create app », puis le dépôt, la branche `main` et le fichier `app.py`.
3. L'application est publiée à une adresse partageable et se met à jour à chaque `git push`.

Attention : si le dépôt ou l'application sont publics, les données le sont aussi.
Garder le dépôt privé tant que les données ne sont pas validées pour diffusion.

## Méthode (résumé)

- Ratio actuel = (emprise × niveaux + annexes) ÷ population actuelle. Ratio futur : choisi, sinon le ratio actuel.
- Besoin brut = ratio futur × population future (scénario de référence, inchangé). Pas de besoin net.
- La part des annexes dans la SBP totale, observée aujourd'hui, est conservée :
  annexes = besoin brut × part ; SBP bâtiments = besoin brut × (1 − part).
- Emprise bâtie = SBP bâtiments ÷ niveaux retenus (entre 1 et le plafond). Sol total = emprise + annexes.
- Les écarts comparent à aujourd'hui et à la référence future (ratio actuel, mêmes niveaux), sans
  hypothèse sur l'existant (construction neuve ou surélévation).

## Sources et limites

- École primaire : règlement genevois RCLEP (rsGE C 1 10.11), annexe ch. 3 et 4
  (4 niveaux au maximum, préaux de 140 m² par classe, soit environ 7 m² par élève).
- Autres équipements : bornes provisoires, à valider par les services concernés.
- Populations futures de référence : valeurs de test (population actuelle + 10 000),
  à remplacer par les projections démographiques par tranche d'âge.
- Piscines, plages et espaces verts ont 0 niveau dans les données : pas de SBP ni d'emprise calculable.
