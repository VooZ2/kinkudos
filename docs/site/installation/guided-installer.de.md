---
title: KinKudos-Schnellinstallation auf einem vorbereiteten Server
description: Installieren Sie KinKudos auf einem vorbereiteten Docker-Server und richten Sie die erste Familie anschließend sicher im Browser ein.
---

# Auf einem vorbereiteten Docker-Server installieren

Dieser Weg ist für eine **neue** KinKudos-Installation auf einem Server gedacht, auf dem Docker Engine, das Docker-Compose-Plugin, eine Domain und ein HTTPS-Reverse-Proxy wie Traefik, Caddy oder Nginx bereits eingerichtet sind.

Sie benötigen einen 64-Bit-Linux-Server (AMD64 oder ARM64), einen auf den Server zeigenden Hostnamen und einen normalen Serverbenutzer mit Docker-Berechtigung. Führen Sie dieses allgemeine Installationsprogramm nicht als `root` aus.

```bash
curl -fsSL https://kinkudos.app/install.sh -o /tmp/kinkudos-install.sh && sh /tmp/kinkudos-install.sh
```

Das Installationsprogramm lädt die neueste veröffentlichte Version, prüft ihre SHA256-Prüfsumme, erstellt die erforderlichen Verzeichnisse und startet die Container. Es fragt nur nach Installationssprache, Hostname und dem bereits vorbereiteten Proxy-Modus.

Am Ende zeigt es eine HTTPS-Adresse mit `/setup/` und einen privaten Einrichtungscode an. Öffnen Sie diese Adresse im Browser und erstellen Sie dort den Familiennamen, das erste Elternkonto, die Sprache und die Zeitzone. SMTP ist optional und kann übersprungen werden. Bewahren Sie den einmalig angezeigten Wiederherstellungscode sicher auf.

Das Programm ersetzt keine vorhandene Installation und erstellt weder DNS-Eintrag noch allgemeinen Reverse-Proxy. Datenbank, Fotos, Sicherungen und Geheimnisse bleiben auf Ihrem Server.

Fahren Sie anschließend mit den [ersten 15 Minuten](../start/first-15-minutes.de.md) fort.
