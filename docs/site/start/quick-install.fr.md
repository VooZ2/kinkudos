# Installer sur un serveur Docker préparé

Utilisez cette procédure pour une **nouvelle** installation de KinKudos sur un
serveur déjà équipé de Docker Engine, du module Docker Compose, d’un domaine et
d’un proxy inverse HTTPS tel que Traefik, Caddy ou Nginx.

> **Pour :** L’administrateur serveur<br>
> **Difficulté :** Administration Linux et Docker<br>
> **Résultat :** Une nouvelle installation KinKudos avec une première famille

Ce guide s’adresse à la personne qui exploite le serveur. Il n’est pas
nécessaire aux parents pour l’utilisation quotidienne.

## Avant de commencer

- un serveur Linux 64 bits (AMD64 ou ARM64) que vous contrôlez ;
- Docker Engine et le module `docker compose` ;
- un nom d’hôte pointant vers le serveur, par exemple `famille.example.com` ;
- un proxy inverse HTTPS configuré pour ce nom d’hôte ;
- un utilisateur serveur normal autorisé à utiliser Docker. N’exécutez pas l’installateur en tant que `root`.

## Exécuter l’installateur

```bash
curl -fsSL https://kinkudos.app/install.sh -o /tmp/kinkudos-install.sh && sh /tmp/kinkudos-install.sh
```

L’installateur télécharge la dernière version publiée, vérifie sa somme SHA256,
crée le répertoire d’installation et lance la configuration guidée. La somme
confirme que l’archive correspond à celle publiée avec la même version ; elle ne
constitue pas une attestation signée indépendante.

La configuration demande la langue, le nom d’hôte, le mode proxy, le nom de la
famille, le premier compte parent et les éventuels profils enfants. Ensuite,
vérifiez l’état des conteneurs et ouvrez le nom d’hôte en HTTPS. En cas de
problème DNS, HTTPS ou de conteneur, utilisez le diagnostic au lieu de relancer
l’installateur sur des fichiers existants.

## Ce que l’installateur ne fait pas

- Il ne remplace pas une installation KinKudos existante.
- Il ne crée ni proxy inverse ni enregistrement DNS.
- Il n’envoie aucune donnée familiale à GitHub ou Docker Hub. La base de données, les photos, les sauvegardes et les secrets restent sur votre serveur.

## Étape suivante

Continuez avec [vos 15 premières minutes](first-15-minutes.fr.md).
