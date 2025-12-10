# Configuration Git Remote - GeoQuizz

Ce guide vous explique comment connecter votre projet GeoQuizz à un dépôt distant (GitHub, GitLab, Bitbucket, etc.).

## Option 1 : GitHub

### 1. Créer un dépôt sur GitHub

1. Allez sur [github.com](https://github.com)
2. Cliquez sur le bouton "+" en haut à droite → "New repository"
3. Nom du dépôt : `GeoQuizz` (ou votre choix)
4. Description : "Application de quiz géographique multijoueur inspirée de GeoGuessr"
5. Choisissez Public ou Private
6. **NE PAS** cocher "Initialize this repository with a README" (vous avez déjà les fichiers)
7. Cliquez sur "Create repository"

### 2. Connecter votre dépôt local

GitHub va vous montrer des commandes. Utilisez celles-ci (adaptées à votre système) :

```bash
# Ajouter le remote
export HOME=/tmp && git remote add origin https://github.com/VOTRE_USERNAME/GeoQuizz.git

# Renommer la branche en main (optionnel, GitHub préfère main au lieu de master)
export HOME=/tmp && git branch -M main

# Pousser le code
export HOME=/tmp && git push -u origin main
```

### 3. Avec SSH (recommandé pour éviter de taper le mot de passe)

Si vous avez configuré une clé SSH sur GitHub :

```bash
export HOME=/tmp && git remote add origin git@github.com:VOTRE_USERNAME/GeoQuizz.git
export HOME=/tmp && git branch -M main
export HOME=/tmp && git push -u origin main
```

## Option 2 : GitLab

### 1. Créer un projet sur GitLab

1. Allez sur [gitlab.com](https://gitlab.com)
2. Cliquez sur "New project" → "Create blank project"
3. Project name : `GeoQuizz`
4. Visibility : Public ou Private
5. Décochez "Initialize repository with a README"
6. Cliquez sur "Create project"

### 2. Connecter votre dépôt local

```bash
# Ajouter le remote
export HOME=/tmp && git remote add origin https://gitlab.com/VOTRE_USERNAME/geoquizz.git

# Renommer la branche (GitLab utilise aussi main)
export HOME=/tmp && git branch -M main

# Pousser le code
export HOME=/tmp && git push -u origin main
```

## Option 3 : Bitbucket

### 1. Créer un dépôt sur Bitbucket

1. Allez sur [bitbucket.org](https://bitbucket.org)
2. Cliquez sur "Create" → "Repository"
3. Repository name : `geoquizz`
4. Access level : Public ou Private
5. Décochez "Include a README"
6. Cliquez sur "Create repository"

### 2. Connecter votre dépôt local

```bash
export HOME=/tmp && git remote add origin https://VOTRE_USERNAME@bitbucket.org/VOTRE_USERNAME/geoquizz.git
export HOME=/tmp && git branch -M main
export HOME=/tmp && git push -u origin main
```

## Option 4 : Serveur Git personnalisé

Si vous avez votre propre serveur Git :

```bash
export HOME=/tmp && git remote add origin ssh://user@votre-serveur.com/chemin/vers/geoquizz.git
export HOME=/tmp && git push -u origin master
```

## Commandes Git essentielles après configuration

### Vérifier les remotes configurés
```bash
export HOME=/tmp && git remote -v
```

### Pousser des changements
```bash
# Après avoir fait des modifications
export HOME=/tmp && git add .
export HOME=/tmp && git commit -m "Description des changements"
export HOME=/tmp && git push
```

### Récupérer les changements
```bash
export HOME=/tmp && git pull
```

### Créer une nouvelle branche pour une fonctionnalité
```bash
export HOME=/tmp && git checkout -b feature/nom-fonctionnalite
export HOME=/tmp && git push -u origin feature/nom-fonctionnalite
```

### Fusionner une branche
```bash
export HOME=/tmp && git checkout main
export HOME=/tmp && git merge feature/nom-fonctionnalite
export HOME=/tmp && git push
```

## Fichiers sensibles

Le fichier `.gitignore` est déjà configuré pour exclure :
- Fichiers Python compilés (`__pycache__`, `*.pyc`)
- Environnement virtuel (`venv/`)
- Données JSON de l'application (`data/*.json`)
- Fichiers IDE (`.vscode/`, `.idea/`)

**Important :** Ne jamais commiter de données sensibles (mots de passe, clés API, etc.)

## Badge pour votre README

Une fois votre dépôt public créé, ajoutez un badge dans votre README :

### GitHub
```markdown
![GitHub](https://img.shields.io/github/stars/VOTRE_USERNAME/GeoQuizz?style=social)
```

### GitLab
```markdown
![GitLab](https://img.shields.io/gitlab/stars/VOTRE_USERNAME/geoquizz?style=social)
```

## Créer un fichier .git-credentials (optionnel)

Pour éviter de retaper votre mot de passe à chaque push :

```bash
export HOME=/tmp && git config credential.helper store
```

**Attention :** Cela stocke votre mot de passe en clair. Utilisez plutôt SSH ou un Personal Access Token.

## Problème de configuration Git (votre cas)

Votre système a un problème avec la configuration globale de Git. Pour chaque commande git, vous devez préfixer avec :

```bash
export HOME=/tmp && [commande git]
```

### Solution permanente

Vous pouvez créer un alias dans votre `.bashrc` ou `.bash_profile` :

```bash
alias git='HOME=/tmp git'
```

Ou créer un script wrapper `mygit.bat` :

```batch
@echo off
set HOME=C:\temp
git %*
```

Ensuite utilisez `mygit` au lieu de `git`.

## Exemple complet : Workflow de développement

```bash
# 1. Créer une branche pour une nouvelle fonctionnalité
export HOME=/tmp && git checkout -b feature/interface-multijoueur

# 2. Faire des modifications dans le code
# ... (éditer les fichiers) ...

# 3. Voir les changements
export HOME=/tmp && git status
export HOME=/tmp && git diff

# 4. Ajouter et commiter
export HOME=/tmp && git add .
export HOME=/tmp && git commit -m "Add multiplayer UI interface"

# 5. Pousser la branche
export HOME=/tmp && git push -u origin feature/interface-multijoueur

# 6. Créer une Pull Request sur GitHub/GitLab
# (via l'interface web)

# 7. Après validation, fusionner dans main
export HOME=/tmp && git checkout main
export HOME=/tmp && git pull
export HOME=/tmp && git merge feature/interface-multijoueur
export HOME=/tmp && git push

# 8. Supprimer la branche (optionnel)
export HOME=/tmp && git branch -d feature/interface-multijoueur
export HOME=/tmp && git push origin --delete feature/interface-multijoueur
```

## Support

Pour plus d'aide sur Git :
- Documentation officielle : https://git-scm.com/doc
- GitHub Docs : https://docs.github.com
- GitLab Docs : https://docs.gitlab.com
