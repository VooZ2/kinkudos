---
title: Installation rapide de KinKudos sur un serveur préparé
description: Installez KinKudos sur un serveur Docker déjà préparé, puis configurez la première famille en toute sécurité dans le navigateur.
---

# Installer sur un serveur Docker préparé

Cette procédure concerne une **nouvelle** installation de KinKudos sur un serveur déjà équipé de Docker Engine, du module Docker Compose, d’un domaine et d’un proxy inverse HTTPS tel que Traefik, Caddy ou Nginx.

Il faut un serveur Linux 64 bits (AMD64 ou ARM64), un nom d’hôte pointant vers ce serveur et un utilisateur normal autorisé à utiliser Docker. N’exécutez pas cet installateur générique en tant que `root`.

```bash
curl -fsSL https://kinkudos.app/install.sh -o /tmp/kinkudos-install.sh && sh /tmp/kinkudos-install.sh
```

L’installateur télécharge la dernière version publiée, vérifie sa somme SHA256, crée les répertoires nécessaires et démarre les conteneurs. Il ne demande que la langue d’installation, le nom d’hôte et le mode du proxy déjà configuré.

À la fin, il affiche une adresse HTTPS se terminant par `/setup/` ainsi qu’un code de configuration privé. Ouvrez cette adresse dans le navigateur pour créer la famille, le premier compte parent, la langue et le fuseau horaire. SMTP est facultatif. Enregistrez le code de récupération à usage unique dans un endroit sûr.

Cette procédure ne remplace pas une installation existante et ne crée ni enregistrement DNS ni proxy inverse générique. La base de données, les photos, les sauvegardes et les secrets restent sur votre serveur.

Continuez ensuite avec [vos 15 premières minutes](../start/first-15-minutes.fr.md).
