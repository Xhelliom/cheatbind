# CLAUDE.md — cheatbind

## Projet

Overlay Wayland qui parse la config du compositor (niri, futur Hyprland/Sway) et affiche un cheatsheet stylisé des raccourcis clavier via GTK4 + layer-shell.

## Stack

- Python 3.11+ / GTK4 / Adwaita / gtk4-layer-shell
- PyGObject bindings
- Pas de framework web, pas de base de données

## Développement

```bash
python3 -m venv .venv && .venv/bin/pip install -e .
.venv/bin/cheatbind
```

## Règles de code

### Limites structurelles

- **Fonctions** : max 40 lignes de code (hors docstring/commentaires). Découper si plus.
- **Fichiers** : max 300 lignes. Découper en modules si plus.
- **Classes** : max 10 méthodes publiques. Au-delà, découper les responsabilités.
- **Paramètres** : max 5 par fonction. Au-delà, utiliser un dataclass ou regrouper.
- **Indentation** : max 4 niveaux de profondeur. Extraire des fonctions si plus.

### Pas de magic numbers / magic strings

- Toute valeur littérale utilisée plus d'une fois → constante nommée en UPPER_SNAKE_CASE.
- Les seuils, tailles, couleurs, délais → constantes en haut du module ou dans config.
- Exception : 0, 1, "", True, False, None sont acceptés inline.

### Nommage

- snake_case pour fonctions, variables, modules.
- PascalCase pour classes.
- UPPER_SNAKE_CASE pour constantes.
- Noms descriptifs — pas d'abréviations cryptiques (sauf i/j/k pour boucles courtes).
- Préfixe `_` pour les attributs/méthodes privés.

### Qualité

- Pas de code mort (commenté ou unreachable).
- Pas de `# TODO` sans issue GitHub associée.
- Pas de `print()` pour le debug — utiliser `logging` si besoin.
- Pas de `type: ignore` sans justification en commentaire.
- Pas de bare `except:` — toujours spécifier les exceptions.
- Pas de mutable default arguments (`def f(x=[])` interdit).
- Imports groupés : stdlib → third-party → local, séparés par une ligne vide.
- Pas d'import wildcard (`from x import *`).

### Sécurité — OWASP / MITRE

#### Entrées et fichiers (OWASP A03 — Injection)

- **Chemins fichiers** : valider et résoudre avec `Path.resolve()` avant lecture. Refuser les chemins contenant `..` provenant d'une source externe.
- **Parsing config** : ne jamais utiliser `eval()`, `exec()`, `pickle.loads()` ou `yaml.load()` (sans SafeLoader) sur du contenu utilisateur.
- **Regex** : attention au ReDoS — pas de quantificateurs imbriqués sur entrée non bornée. Préférer des patterns linéaires.
- **Subprocess** : ne jamais passer `shell=True` avec des données variables. Utiliser des listes d'arguments.

#### Exécution (MITRE T1059 — Command Execution)

- Pas de `os.system()` — utiliser `subprocess.run()` avec une liste d'arguments.
- Pas d'exécution de commandes construites par concaténation de strings.
- Le PID file ne doit jamais être dans un répertoire world-writable sans vérification de propriétaire.

#### Fichiers et permissions (MITRE T1083 — File Discovery / OWASP A01 — Broken Access)

- PID file dans `$XDG_RUNTIME_DIR` uniquement (permissions user-only par défaut).
- Ne pas suivre les symlinks pour les fichiers de config sans vérifier la destination.
- Vérifier que les fichiers lus sont des fichiers réguliers (`Path.is_file()`).

#### Signaux et IPC (MITRE T1559)

- `os.kill()` uniquement sur des PID lus depuis un fichier dont on est propriétaire.
- Vérifier que le PID correspond bien à un processus cheatbind avant de le tuer (race condition sinon).

#### Dépendances (OWASP A06 — Vulnerable Components)

- Minimum de dépendances. PyGObject est la seule dépendance Python.
- Pas de dépendances réseau à l'exécution.
- Vérifier les CVE des dépendances périodiquement.

#### Déni de service

- Limiter la taille des fichiers config parsés (refuser > 1 Mo).
- Timeout ou limite d'itérations sur le parsing pour éviter les boucles infinies sur config malformée.

### CSS / GTK

- Pas de couleurs en rgba() sur les éléments au premier plan (problème de lisibilité avec la transparence de l'overlay).
- Couleurs opaques pour les éléments interactifs et les key pills.
- Utiliser des variables CSS ou des constantes pour les couleurs récurrentes.
