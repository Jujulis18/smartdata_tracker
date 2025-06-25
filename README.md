# SmartData Tracker

## Objectif du Projet

L'objectif de SmartData Tracker est de fournir une solution innovante pour aider les entreprises à rester informées des dernières tendances et développements dans leur domaine. En automatisant le processus de veille, cet outil permet aux entreprises de gagner du temps et des ressources, tout en améliorant leur prise de décision et leur avantage concurrentiel.

## Valeur Ajoutée

- **Automatisation du Processus de Veille** : Gain de temps en évitant la recherche manuelle d'articles et efficacité accrue en parcourant et extrayant des articles de multiples sites web en un temps record.
- **Organisation et Gestion des Articles** : Catégorisation des articles pour une meilleure gestion et recherche d'informations, et filtrage des articles par catégories pour une recherche d'informations plus efficace.
- **Visualisation et Export des Données** : Visualisation interactive des articles pour une analyse et une prise de décision facilitée, et export des données en CSV et Excel pour une analyse ultérieure et la création de rapports.
- **Scalabilité et Maintenabilité** : Conçu pour être scalable, capable de gérer un grand nombre de sites web et d'articles sans perte de performance, avec une architecture modulaire facilitant la maintenance et les mises à jour.

## Table des Matières

- [Introduction](#introduction)
- [Fonctionnalités](#fonctionnalités)
- [Architecture du Projet](#architecture-du-projet)

## Introduction

SmartData Tracker vise à automatiser le processus de veille sur des sites web, en extrayant des articles et en les organisant par catégories. Cela permet aux entreprises de rester informées des dernières tendances et développements dans leur domaine, sans avoir à consacrer du temps à la recherche manuelle.


## Fonctionnalités

- Extraction automatique des articles à partir de sites web.
- Organisation des articles par catégories pour une meilleure gestion.
- Interface utilisateur interactive pour visualiser et filtrer les articles.
- Export des données en CSV et Excel pour une analyse ultérieure.

## Architecture du Projet

### Étape 1: Sélection du Site et Configuration des Locateurs

- **Sélection du site** : Vous avez un lien vers le site et un lien vers le dernier article posté.
- **Agent LeChat** : Cet agent va parcourir la page pour déterminer les locateurs utiles.
  - **Locateurs à récupérer** :
    - Titre
    - Résumé
    - Lien
    - Date (optionnelle)
    - Bouton "Next" ou "Previous"
  - **Configuration Output Format** :
    ```json
    {
      "url": "URL du site",
      "locatorTitle": "Locateur pour le titre",
      "locatorDescription": "Locateur pour le résumé",
      "locatorDate": "Locateur pour la date",
      "locatorLink": "Locateur pour le lien",
      "locatorNextPage": "Locateur pour le bouton Next/Previous",
      "category": "Catégorie du site"
    }
    ```

### Étape 2: Script Python pour Itérer sur les Pages

- **Script Python** : Ce script va utiliser les locateurs pour récupérer les articles.
  - **Fonctionnalités** :
    - Itérer sur les pages
    - Récupérer les articles avec leurs informations
    - Être générique pour utiliser des locateurs basés sur des ID ou des classes
  - **Output Format** :
    ```csv
    id, title, description, link, date, category
    ```

### Étape 3: Sauvegarder les Informations dans un Excel

- **Sauvegarde** : Les informations récupérées seront sauvegardées dans un fichier Excel.

### Étape 4: Ajout de Tags aux Catégories

- **Agent LeChat** : L'agent va déterminer et ajouter des tags à la colonne "category" pour spécifier le thème.
  - **Liste des Thèmes** : Une liste des thèmes sera enrichie au fur et à mesure pour utiliser le même vocabulaire et mieux organiser les données.
  - **Theme Format** :
    ```csv
    tags, main_category, date
    ```

### Étape 5: Extraction des Nouveaux Articles

- **Script Python** : Ce script va extraire les nouveaux articles sur une période donnée (semaine ou mois).
  - **Input** : Même configuration que précédementt
  - **Fonctionnalités** :
    - Si pas de locator date, étape supplémentaire pour trouver la date dans l'article
  - **Output Format** : Même format csv
  - **Sauvegarde** : Possibilité de sauvegarder sur Excel

### Étape 6: Interfaces Utilisateur

- **Interface d'Extraction** :
  - Un formulaire pour entrer l'URL.
  - Un bouton pour lancer l'extraction.
  - Un aperçu des données avant la sauvegarde.

- **Interface de Visualisation** :
  - Une table pour afficher les articles avec des filtres multiples par catégories.
  - Des boutons pour des actions rapides (par exemple, sauvegarde sur Excel).


