# Contributing to GeoQuizz

Merci de votre intérêt pour contribuer à GeoQuizz ! Toutes les contributions sont les bienvenues.

## Comment contribuer

### Signaler des bugs

Si vous trouvez un bug, ouvrez une issue avec :
- Description du problème
- Étapes pour reproduire
- Comportement attendu vs comportement actuel
- Environnement (OS, version Python, navigateur)
- Captures d'écran si pertinent

### Proposer des fonctionnalités

Pour proposer une nouvelle fonctionnalité :
1. Ouvrez une issue pour en discuter
2. Expliquez le cas d'usage
3. Proposez une implémentation si possible

### Soumettre des Pull Requests

1. **Fork le projet**
   ```bash
   # Cliquez sur "Fork" sur GitHub
   git clone https://github.com/VOTRE_USERNAME/GeoQuizz.git
   cd GeoQuizz
   ```

2. **Créer une branche**
   ```bash
   git checkout -b feature/ma-nouvelle-fonctionnalite
   ```

3. **Faire vos modifications**
   - Écrivez du code propre et commenté
   - Suivez les conventions Python (PEP 8)
   - Testez vos changements

4. **Commiter**
   ```bash
   git add .
   git commit -m "Add: description de la fonctionnalité"
   ```

5. **Pousser et créer une PR**
   ```bash
   git push origin feature/ma-nouvelle-fonctionnalite
   ```
   Puis créez une Pull Request sur GitHub

## Style de code

### Python
- Suivre PEP 8
- Utiliser des noms de variables explicites
- Ajouter des docstrings pour les fonctions
- Commenter le code complexe

### JavaScript
- Utiliser camelCase pour les variables
- Commenter les fonctions importantes
- Éviter le code répétitif

### CSS
- Organiser par sections
- Utiliser des noms de classes descriptifs
- Préférer les unités relatives (rem, %)

## Structure des commits

Utilisez des messages de commit clairs :

```
Type: Description courte

Description détaillée si nécessaire

Exemples de types:
- Add: Nouvelle fonctionnalité
- Fix: Correction de bug
- Update: Mise à jour de fonctionnalité
- Refactor: Refactorisation du code
- Docs: Documentation
- Style: Formatage, style
- Test: Tests
```

## Idées de contributions

### Fonctionnalités
- [ ] Interface web pour le mode multijoueur
- [ ] Support WebSocket pour le temps réel
- [ ] Mode de jeu "Street View"
- [ ] Système de niveaux et achievements
- [ ] Thèmes (dark mode)
- [ ] Support multilingue (i18n)
- [ ] Export des résultats en PDF
- [ ] Intégration avec OAuth (Google, Facebook)

### Améliorations techniques
- [ ] Tests unitaires (pytest)
- [ ] Tests d'intégration
- [ ] Cache pour les photos
- [ ] Optimisation des performances
- [ ] Migration vers PostgreSQL (optionnel)
- [ ] API GraphQL (alternative REST)
- [ ] Documentation API avec Swagger

### Documentation
- [ ] Tutoriels vidéo
- [ ] Traductions (anglais, espagnol, etc.)
- [ ] Guide de contribution plus détaillé
- [ ] FAQ

## Processus de review

1. Un mainteneur examinera votre PR
2. Des commentaires peuvent être faits
3. Effectuez les modifications demandées
4. Une fois approuvée, la PR sera mergée

## Code de conduite

- Soyez respectueux et constructif
- Accueillez les nouveaux contributeurs
- Focalisez sur le code, pas sur les personnes
- Aidez les autres à apprendre

## Questions

Pour toute question, n'hésitez pas à :
- Ouvrir une issue
- Demander dans les Pull Requests
- Contacter les mainteneurs

Merci de contribuer à GeoQuizz ! 🌍
