# Comprendre l’auto-hébergement

L’auto-hébergement signifie que votre famille — et non KinKudos — exploite le
serveur qui conserve l’application et les données familiales privées. Vous
gardez le contrôle, mais assumez aussi la responsabilité du serveur.

> **Pour :** La personne qui organise la maintenance de KinKudos<br>
> **Difficulté :** Administration système de base<br>
> **Prérequis :** Linux, Docker, un nom d’hôte, HTTPS et un plan de sauvegarde

## La famille est responsable de

- maintenir le serveur, le domaine, le proxy HTTPS et Docker ;
- protéger les identifiants du serveur et des fournisseurs ;
- installer la dernière version de KinKudos ;
- configurer et vérifier les sauvegardes ;
- choisir les administrateurs de la famille et du serveur.

KinKudos conserve les données dans votre installation, mais ne peut pas
protéger un serveur non mis à jour, exposé publiquement par erreur ou perdu sans
sauvegarde utilisable.

## Ce qui n’est pas nécessaire le premier jour

La messagerie SMTP, les sauvegardes distantes et les restrictions d’adresse IP
sont des options utiles. Elles ne sont pas nécessaires pour créer des tâches,
associer un appareil enfant ou utiliser les points et récompenses.

## Répartition pratique des responsabilités

| Personne | Responsabilité habituelle |
| --- | --- |
| **Parent** | Utilise les tâches, récompenses, validations et réglages familiaux ordinaires. |
| **Administrateur parent** | Gère les réglages sensibles, les appareils associés et les comptes familiaux. |
| **Administrateur serveur** | Gère Docker, HTTPS, les mises à jour, les identifiants de stockage, les sauvegardes et la restauration. Une personne peut cumuler les trois rôles. |

## Étape suivante

Vérifiez les [prérequis du serveur](../installation/guided-installer.fr.md) ou commencez à utiliser
une installation existante avec [vos 15 premières minutes](first-15-minutes.fr.md).

[Retour au démarrage rapide →](../index.fr.md)
