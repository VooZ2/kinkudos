# Pranešimai ir KinKudos diegimas

KinKudos galima įdiegti kaip PWA programą ir ji gali siųsti naršyklės pranešimus. Abu dalykai pasirenkami ir nustatomi atskirai kiekviename telefone, planšetėje, kompiuteryje ar naršyklėje.

## Įdiekite KinKudos

Įdiegus KinKudos gauna atskirą programos arba pradžios ekrano ikoną; „iPhone“ ir „iPad“ įdiegimas būtinas pranešimams.

- **iPhone / iPad:** atidarykite KinKudos per „Safari“, pasirinkite **Share**, tada **Add to Home Screen**. Prieš įjungdami pranešimus bent kartą atidarykite įdiegtą programą.
- **Android:** atidarykite svetainę per „Chrome“, naršyklės meniu pasirinkite **Install app** arba **Add to Home screen**.
- **Kompiuteris:** „Chrome“ ar „Edge“ naudokite diegimo ikoną adreso juostoje arba meniu punktą **Install**.

## Įjunkite pranešimus

Prisijunkite tame įrenginyje, viršutinėje juostoje spauskite varpelį ir patvirtinkite naršyklės leidimą. Pakartokite kiekviename įrenginyje, kuriame norite gauti pranešimus. Aktyvus tėvas gauna pranešimus apie vaikų pateiktus darbus, prizų prašymus, pasiūlymus ir gimtadienio keitimo prašymus; vaikai – apie tėvų sprendimus, paskirtus darbus, dovanas, gimtadienio taškus ir pasirinktiną nutrinamų bilietų priminimą. Išjungus tėvų paskyrą panaikinamos jos „push“ prenumeratos, todėl ji nebegaus tėvams skirtų pranešimų.

Pranešimai siunčiami geriausiu bandymu po duomenų bazės commit fone, su griežtu endpoint timeout; lėtas ar nepavykęs push veiksmo nesužlugdo. Būseną visada tikrinkite pačioje programoje.

Naršyklės prenumerata turi naudoti įprastą viešą HTTPS „Web Push“ endpointą.
Akivaizdžiai netinkami, vietiniai, privatūs ar ne HTTPS endpointai atmetami. Jei
varpelis praneša, kad įjungti nepavyko, patikrinkite naršyklės/svetainės
pranešimų leidimą, „iPhone/iPad“ atidarykite įdiegtą PWA, patikrinkite internetą
ir bandykite dar kartą iš viešo HTTPS adreso. Atšaukus vaiko įrenginį, jo
pranešimų prenumerata panaikinama. Pranešimai yra patogumas – esamą būseną visada
tikrinkite pačioje programoje.
