# Auf einem vorbereiteten Docker-Server installieren

Dieser Weg ist für eine **neue** KinKudos-Installation auf einem Server gedacht,
auf dem Docker Engine, das Docker-Compose-Plugin, eine Domain und ein
HTTPS-Reverse-Proxy wie Traefik, Caddy oder Nginx bereits eingerichtet sind.

> **Für:** Serveradministration<br>
> **Schwierigkeit:** Linux- und Docker-Administration<br>
> **Ergebnis:** Eine neue KinKudos-Installation mit erster Familieneinrichtung

Diese Anleitung richtet sich an die Person, die den Server betreibt. Eltern
benötigen sie nicht für die tägliche Nutzung.

## Voraussetzungen

- ein selbst kontrollierter 64-Bit-Linux-Server (AMD64 oder ARM64);
- Docker Engine und das Plugin `docker compose`;
- ein auf den Server zeigender Hostname, zum Beispiel `familie.example.com`;
- ein HTTPS-Reverse-Proxy für diesen Hostnamen; und
- ein normaler Serverbenutzer mit Docker-Berechtigung. Führen Sie das Installationsprogramm nicht als `root` aus.

## Installationsprogramm ausführen

```bash
curl -fsSL https://kinkudos.app/install.sh -o /tmp/kinkudos-install.sh && sh /tmp/kinkudos-install.sh
```

Das Installationsprogramm lädt die neueste veröffentlichte Version, prüft ihre
SHA256-Prüfsumme, erstellt das Installationsverzeichnis und startet die geführte
Einrichtung. Die Prüfsumme bestätigt, dass das Archiv der mit derselben Version
veröffentlichten Prüfsumme entspricht; sie ist keine separate signierte
Bestätigung.

Die Einrichtung fragt nach Sprache, Hostname, Proxy-Modus, Familienname, dem
ersten Elternkonto und optionalen Kinderprofilen. Prüfen Sie danach den
Containerstatus und öffnen Sie den Hostnamen über HTTPS. Bei Problemen mit DNS,
HTTPS oder Containern verwenden Sie die Diagnose, statt das Installationsprogramm
erneut über vorhandene Dateien auszuführen.

## Was das Installationsprogramm nicht erledigt

- Es ersetzt keine vorhandene KinKudos-Installation.
- Es erstellt weder Reverse-Proxy noch DNS-Eintrag.
- Es sendet keine Familiendaten an GitHub oder Docker Hub. Datenbank, Fotos, Sicherungen und Geheimnisse bleiben auf Ihrem Server.

## Nächster Schritt

Fahren Sie mit den [ersten 15 Minuten](first-15-minutes.de.md) fort.
