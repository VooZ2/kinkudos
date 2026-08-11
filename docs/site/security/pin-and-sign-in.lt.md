# PIN ir prisijungimo apsauga

KinKudos tėvams ir vaikams naudoja skirtingus prisijungimo būdus, nes jų prieigos teisės skiriasi.

## Tėvų prisijungimas

Kiekvienas tėvas naudoja atskirą naudotojo vardą ir slaptažodį. Slaptažodis turi būti bent 12 simbolių ir pereiti „Django“ patikrą: jis negali būti dažnas, vien tik skaitinis ar pernelyg panašus į naudotojo vardą. Slaptažodžiai saugomi kaip saugios maišos, o ne perskaitomas tekstas.

Kiekvienam suaugusiajam sukurkite atskirą paskyrą. Nesidalinkite tėvų slaptažodžiu su vaiku, net jei jis žino įrenginio PIN.

Tėvai savo paskyros duomenis gali keisti per **Tėvai → Nustatymai → Paskyros**,
po antrašte **Tėvų paskyros**. Slaptažodžio atkūrimas el. paštu veikia tik
administratoriui sukonfigūravus SMTP.

### Atkurti tėvų slaptažodį

Tėvų prisijungimo puslapyje pasirinkite **Pamiršote slaptažodį?**, įrašykite aktyvios tėvų paskyros el. pašto adresą ir iš laiško nuorodos nustatykite naują slaptažodį. Kol SMTP išjungtas, šis puslapis sąmoningai nepasiekiamas. Negavę laiško, pirmiausia patikrinkite šlamštą, tada paprašykite administratoriaus patikrinti SMTP – nekurkite pakaitinės paskyros vien tam, kad atgautumėte prieigą.

## Vaiko PIN logika

Vaikas jungiasi tiksliai keturių skaitmenų PIN kodu, tačiau tik iš [susieto įrenginio](../start/pair-a-child-device.lt.md). PIN saugomas kaip saugi maiša ir po nustatymo niekada nerodomas nei tėvams, nei vaikui.

PIN ekraną saugo keli lygiai:

- įrenginys turi būti susietas, kad išvis galėtų rodyti vaikų profilius arba priimti PIN;
- neteisingi bandymai ribojami pagal profilį, įrenginį, IP adresą ir visą svetainę;
- po penkių neteisingų bandymų vieno vaiko profilis užrakinamas penkioms minutėms; ir
- tėvas gali paspausti **Atrakinti profilį** vaiko kortelėje, nelaukdamas.

Pakeitus PIN, senasis iškart nustoja galioti. Atšaukus įrenginį, tame įrenginyje vaiko prieiga panaikinama; grįžti galima tik susiejus įrenginį iš naujo ir įvedus dabartinį PIN.

## Paprasta šeimos taisyklė

Laikykite vaiko PIN privačiu kodu, o ne bendra šeimos paslaptimi. Susiekite tik šeimai priklausančius įrenginius. Pametus, pardavus, ilgam paskolinus ar ne šeimos žmogui naudojant įrenginį, prieigą iškart atšaukite.

## Tėvų administratorius

Pirmas diegimo metu sukurtas tėvas yra tėvų administratorius. Jis turi įprastas tėvų teises ir papildomai gali keisti tinklo ribojimus, SMTP, nuotolinių kopijų prisijungimo duomenis, paleisti rankinę kopiją ir atšaukti visus vaikų įrenginius. Kiti tėvai vis tiek gali naudoti kasdienį tėvų meniu, valdyti įprastas tėvų paskyras ir matyti kopijų būseną, tačiau negali redaguoti ar išjungti administratoriaus paskyros. Paskutinio aktyvaus administratoriaus išjungti negalima.

[Paskyros ir įrenginiai →](accounts-and-devices.lt.md) · [Tinklo prieiga →](network-access.lt.md)
