# Was Selbsthosting bedeutet

Selbsthosting bedeutet, dass Ihre Familie — nicht KinKudos — den Server mit der
Anwendung und den privaten Familiendaten betreibt. Das schafft Kontrolle, aber
auch Verantwortung.

> **Für:** Die Person, die die Wartung von KinKudos plant<br>
> **Schwierigkeit:** Grundkenntnisse in der Serververwaltung<br>
> **Benötigt:** Linux, Docker, Hostname, HTTPS und ein Sicherungskonzept

## Die Familie ist verantwortlich für

- den Betrieb von Server, Domain, HTTPS-Proxy und Docker;
- den Schutz der Server- und Anbieterzugangsdaten;
- die Installation der neuesten KinKudos-Version;
- die Einrichtung und Prüfung von Sicherungen; und
- die Vergabe der Familien- und Serveradministration.

KinKudos hält Anwendungsdaten innerhalb der Installation privat. Es kann jedoch
keinen ungepatchten, versehentlich öffentlich erreichbaren oder ohne nutzbare
Sicherung verlorenen Server schützen.

## Was am ersten Tag nicht nötig ist

SMTP-E-Mail, entfernte Sicherungen und IP-Einschränkungen sind nützliche
optionale Dienste. Sie sind nicht erforderlich, um Aufgaben anzulegen, ein
Kindergerät zu verbinden oder Punkte und Belohnungen zu verwenden.

## Praktische Rollenverteilung

| Person | Normale Verantwortung |
| --- | --- |
| **Elternteil** | Verwendet Aufgaben, Belohnungen, Freigaben und gewöhnliche Familieneinstellungen. |
| **Elternadministrator** | Verwaltet sensible App-Einstellungen, verbundene Geräte und Familienkonten. |
| **Serveradministrator** | Verwaltet Docker, HTTPS, Updates, Speicherzugänge, Sicherungen und Wiederherstellung. Eine Person kann alle Rollen übernehmen. |

## Nächster Schritt

Prüfen Sie die [Anforderungen an den vorbereiteten Server](quick-install.de.md)
oder beginnen Sie bei einer vorhandenen Installation mit den
[ersten 15 Minuten](first-15-minutes.de.md).

[Zurück zum Schnellstart →](../index.de.md)
