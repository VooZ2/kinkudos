# KinKudos

<p align="center">
  <strong>Kasdienius šeimos darbus paverskite bendrais pasiekimais.</strong><br>
  Privati, savarankiškai diegiama programa, kurioje vaikai atlieka darbus,
  renka teminius taškus ir renkasi prizus, o tėvai viską valdo paprastai bei sąžiningai.
</p>

<p align="center">
  <a href="https://demo.kinkudos.app/"><strong>🚀 Išbandyti demonstraciją</strong></a>
  ·
  <a href="https://kinkudos.app/">🌐 Apsilankyti svetainėje</a>
  ·
  <a href="README.md">🇬🇧 In English</a>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="MIT licencija"></a>
  <a href="https://github.com/VooZ2/kinkudos/releases"><img src="https://img.shields.io/github/v/release/VooZ2/kinkudos?display_name=release" alt="Naujausias GitHub leidimas"></a>
</p>
<p align="center"><sub>Dabartinis leidimas: 26.4.9</sub></p>

---

## ✨ Kaip tai atrodo

<table>
  <tr>
    <td width="50%"><img src="docs/screenshots/parent-dashboard-2026.png" alt="KinKudos tėvų suvestinė su laukiančiais prašymais"></td>
    <td width="50%"><img src="docs/screenshots/parent-settings-2026.png" alt="KinKudos tėvų nustatymai"></td>
  </tr>
  <tr>
    <td align="center"><sub><strong>Tėvų suvestinė</strong><br>Peržiūrėkite prašymus ir priimkite sprendimus vienoje vietoje.</sub></td>
    <td align="center"><sub><strong>Šeimos valdymas</strong><br>Tvarkykite prizus, loterijos nustatymus, privatumą ir paslaugas.</sub></td>
  </tr>
</table>

<table>
  <tr>
    <td width="50%"><img src="docs/screenshots/child-panda-dashboard-2026.png" alt="KinKudos Panda Pet vaiko suvestinė"></td>
    <td width="50%"><img src="docs/screenshots/child-block-world-dashboard-2026.png" alt="KinKudos Block World vaiko suvestinė"></td>
  </tr>
  <tr>
    <td align="center"><sub><strong>Savas pasaulis</strong><br>Vaikas gali pasirinkti temą, kuri pažangą paverčia asmeniška.</sub></td>
    <td align="center"><sub><strong>Darbai, prizai ir tikslai</strong><br>Kasdieniai įpročiai tampa aiškiomis misijomis ir matoma pažanga.</sub></td>
  </tr>
</table>

<p align="center">
  <img src="docs/screenshots/mobile-welcome-2026.png" width="31%" alt="KinKudos mobilus pradžios ekranas">
  <img src="docs/screenshots/mobile-parent-dashboard-2026.png" width="31%" alt="KinKudos mobili tėvų suvestinė">
</p>
<p align="center"><sub>Įsidiekite KinKudos kaip PWA ir rūpinkitės šeimos kasdienybe telefone ar planšetėje.</sub></p>

Ekrano nuotraukose naudojami išgalvoti demonstraciniai duomenys.

## 🚀 Išbandykite demonstraciją

Susipažinkite su KinKudos nieko nediegdami:

- **Demonstracija:** [demo.kinkudos.app](https://demo.kinkudos.app/)
- **Tėvų paskyra:** `demo` / `demo`
- **Vaiko PIN:** `1234`

Vieša demonstracija reguliariai atkuriama, todėl galite drąsiai išbandyti.

## 🎯 Ką gali šeima

- ✅ **Paverskite darbus pažanga** — vaikai pasirenka arba gauna darbus, pateikia atliktą darbą, o tėvai jį patvirtina.
- 🎨 **Suteikite asmeniškumo** — septynios originalios vaikų temos turi savo vaizdus, tekstus, garsus ir taškų vienetus.
- 🎁 **Kurti sveikus įpročius su prizais** — prizai, taupymo tikslai, dovanos, gimtadienio taškai ir tėvų patvirtinami pasiūlymai.
- 🎟️ **Pridėkite netikėtumo** — pasirenkami nutrinami loterijos bilietai su aiškiomis tikimybėmis, limitais ir tėvų valdikliais.
- 📷 **Dalinkitės privačiomis darbų nuotraukomis** — jos sumažinamos, konvertuojamos į WebP ir prieš saugojimą išvalomos nuo EXIF metaduomenų.
- 🔔 **Išlikite informuoti** — pasirinktiniai „Web Push“ pranešimai apie sprendimus, prašymus, paskyrimus ir priminimus.
- 📱 **Naudokite namuose bet kuriame įrenginyje** — įdiegiama PWA telefonuose, planšetėse ir kompiuteriuose.
- 🌍 **Pasirinkite kalbą** — tėvų ir vaikų sąsaja pateikiama lietuvių ir anglų kalbomis.
- 🔐 **Išlaikykite šeimos duomenų privatumą** — viena instaliacija skirta vienai šeimai; programoje nėra reklamų ar integruotos analitikos.

## 🛡️ Privati šeimos erdvė

KinKudos skirta diegti nuosavame serveryje, už pasirinkto HTTPS reverse proxy.

- Tėvų paskyros naudoja bandymų skaičių ribojančius slaptažodžius.
- Vaikai jungiasi susietu įrenginiu ir PIN su bandymų limitu.
- Taškų operacijos yra transakcinės ir įrašomos į nekintamą žurnalą.
- Nuotraukos, duomenų bazės, kopijos ir prisijungimo duomenys laikomi už viešos repozitorijos ribų.
- Pasirenkamos šifruotos kopijos palaiko „Backblaze B2“ ir S3 suderinamas saugyklas.

Plačiau skaitykite [architektūros ir saugumo apžvalgoje](docs/ARCHITECTURE.md).

## ⚡ Greitas diegimas

KinKudos diegiama su Docker Compose ARM64 arba AMD64 Linux serveryje.

Naujame serveryje, kuriame jau veikia „Docker Engine“ ir „Docker Compose“
papildinys:

```bash
curl -fsSL https://kinkudos.app/install.sh -o /tmp/kinkudos-install.sh && sh /tmp/kinkudos-install.sh
```

Nedidelis diegiklis parsisiunčia naujausią paskelbtą leidimą, patikrina jo
SHA256 kontrolinę sumą ir paleidžia esamą vedamą paruošimą. Jis skirtas naujai
KinKudos instaliacijai; esamos instaliacijos atnaujinamos pagal atskirą gidą.

1. **Paruoškite serverį** su Docker, Docker Compose, domenu ir TLS reverse proxy.
2. **Paleiskite vedlį** iš paskelbto leidimo.
3. **Sukurkite šeimą** — diegiklis gali sukurti pirmą tėvų paskyrą ir vaikų profilius.

👉 **[Atidaryti visą diegimo ir atnaujinimo gidą](deploy/README.lt.md)**

Gide aprašytas Docker diegimas, leidimo patikra, Caddy/Nginx/Traefik ir konteinerinių proxy variantai, pirmos šeimos sukūrimas, atnaujinimai, kopijos ir diagnostika.

### 🖥️ Neturite serverio namuose?

Šeimai, neturinčiai namų serverio, mažas VPS yra paprasčiausias būdas privačiai naudoti KinKudos internete. Rekomenduojame Docker tinkamą [Hostinger VPS](https://www.hostinger.com/lt?REFERRALCODE=LKIGEDIMICSU) *(referral nuoroda)* ir tą patį [visą diegimo gidą](deploy/README.lt.md).

## 🧑‍💻 Vietinis kūrimas

Reikalingas Python 3.12. Sukūrus virtualią aplinką ir įdiegus `requirements.txt`:

```bash
python scripts/compile_translations.py
python manage.py migrate
python manage.py test economy.tests
python manage.py runserver
```

`seed_demo` skirta tik kūrimui ir atsisako keisti netuščią duomenų bazę.

## 🤝 Atsiliepimai ir pagalba

Radote problemą ar turite idėją?

- Naudokite programoje esančią atsiliepimų formą, kad privačiai pasidalintumėte su šeimos administratoriumi.
- [Atidarykite GitHub problemą](https://github.com/VooZ2/kinkudos/issues), jei radote pakartojamą programos klaidą.
- Peržiūrėkite [pakeitimų istoriją](CHANGELOG.lt.md), kad sužinotumėte, kas keitėsi kiekviename leidime.

## 📄 Licencija

KinKudos yra atvirojo kodo programa, platinama pagal [MIT licenciją](LICENSE).

## ⚠️ Atsakomybės apribojimas

KinKudos yra AI sukurtas asmeninis projektas, skirtas tik išbandyti OpenAI Codex. Jis pateikiamas toks, koks yra, be garantijų, palaikymo pažado ar patvirtinimo, kad tinka konkrečiam naudojimui arba yra visiškai saugus.
