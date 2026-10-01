# DMX-Kanalbelegung: Blazor, KLS Laser Bar Pro, Inno Pocket Spot

Stand 01.10.2026. Kanal-Modus jeweils so, wie er in SoundSwitch (Projekt `DJ_eMPi`) eingestellt ist.
Werte aus den Herstellerhandbüchern, Quellen am Ende.

| Gerät | Hersteller | Modus in SoundSwitch | Handbuch |
|---|---|---|---|
| Blazor | Chauvet DJ | 11 Kanäle | User Manual Rev. 3, S. 10–11 |
| LED KLS Laser Bar Pro (FX Light Set) | Eurolite | 28 Kanäle | Art.-Nr. 51741091, S. 19 (deutsch) |
| Inno Pocket Spot | ADJ (American DJ) | 11 Kanäle | User Instructions Rev. 3/14, S. 22–23 |

---

## Chauvet DJ Blazor – 11-Kanal-Modus

| Kanal | Funktion | Wert | Bedeutung |
|---|---|---|---|
| 1 | Auto-Programm | 001–127 | Auto-Modus |
| | | 128–255 | Sound-Modus |
| 2 | Auto-Geschwindigkeit / Sound-Empfindlichkeit | 000–255 | langsam → schnell (Auto) bzw. 0–100 % (Sound), je nach Kanal 1 |
| 3 | Dimmer | 000–255 | 0–100 % |
| 4 | Strobe | 000–015 | offen |
| | | 016–255 | Strobe langsam → schnell |
| 5 | Farbe | 000–009 | Weiß |
| | | 010–019 | Rot |
| | | 020–029 | Grün |
| | | 030–039 | Blau |
| | | 040–049 | Gelb |
| | | 050–059 | Amber |
| | | 060–069 | Magenta |
| | | 070–079 | Magenta + Weiß |
| | | 080–089 | Magenta + Amber |
| | | 090–099 | Amber + Gelb |
| | | 100–109 | Gelb + Blau |
| | | 110–119 | Blau + Grün |
| | | 120–129 | Grün + Rot |
| | | 130–139 | Rot + Weiß |
| | | 140–197 | Farbwechsel im Uhrzeigersinn, schnell → langsam |
| | | 198–255 | Farbwechsel gegen Uhrzeigersinn, schnell → langsam |
| 6 | Gobo | 000–019 | Gobo 1 |
| | | 020–039 | Gobo 2 |
| | | 040–059 | Gobo 3 |
| | | 060–079 | Gobo 4 |
| | | 080–099 | Gobo 5 |
| | | 100–119 | Gobo 6 |
| | | 120–139 | Gobo 7 |
| | | 140–197 | Gobo-Wechsel im Uhrzeigersinn, schnell → langsam |
| | | 198–255 | Gobo-Wechsel gegen Uhrzeigersinn, schnell → langsam |
| 7 | Gobo-Rotation | 001–042 | Gobo-Index |
| | | 043–086 | Stopp |
| | | 087–129 | Rotation langsam → schnell |
| | | 130–222 | Stopp |
| | | 223–255 | Wechselrotation links/rechts, langsam → schnell |
| 8 | Spiegel-Rotation | 001–086 | im Uhrzeigersinn, langsam → schnell |
| | | 087–129 | Stopp |
| | | 130–222 | gegen Uhrzeigersinn, langsam → schnell |
| | | 223–255 | Spiegel-Bounce, langsam → schnell |
| 9 | Barrel-Rotation | 001–086 | Barrel-Scroll langsam → schnell |
| | | 087–129 | Stopp |
| | | 130–222 | Barrel-Scroll rückwärts, langsam → schnell |
| | | 223–255 | Barrel-Bounce, langsam → schnell |
| 10 | Barrel-Pan | 000–128 | Position 0–100 % |
| | | 129–255 | Pan-Bounce, langsam → schnell |
| 11 | Steuerung | 000–095 | keine Funktion |
| | | 096–103 | Pan-Reset |
| | | 104–111 | Tilt-Reset |
| | | 112–119 | Farbrad-Reset |
| | | 120–127 | Goborad-Reset |
| | | 128–151 | Reset alles |
| | | 152–255 | keine Funktion |

Hinweis: Kanäle 1, 7, 8, 9 beginnen im Handbuch bei 001 – was 000 bewirkt, ist nicht angegeben.

---

## Eurolite LED KLS Laser Bar Pro – 28-Kanal-Modus

Quelle ist die deutsche Tabelle. Die englische Tabelle im selben Handbuch ist bei den
Kanälen 4/5 und 19/20 um eine Zeile verrutscht und dort falsch.

| Kanal | Teil | Funktion | Wert | Bedeutung |
|---|---|---|---|---|
| 1 | Derby 1 | Rot | 000–255 | 0–100 % |
| 2 | Derby 1 | Grün | 000–255 | 0–100 % |
| 3 | Derby 1 | Blau | 000–255 | 0–100 % |
| 4 | Derby 1 | Strobe | 000–009 | keine Funktion |
| | | | 010–255 | Strobe langsam → schnell (30 Hz) |
| 5 | Derby 1 | Rotation | 000–004 | keine Rotation |
| | | | 005–127 | vorwärts langsam → schnell |
| | | | 128–133 | keine Rotation |
| | | | 134–255 | rückwärts langsam → schnell |
| 6 | Spot 2 | Rot | 000–255 | 0–100 % |
| 7 | Spot 2 | Grün | 000–255 | 0–100 % |
| 8 | Spot 2 | Blau | 000–255 | 0–100 % |
| 9 | Spot 2 | Strobe | 000–009 | keine Funktion |
| | | | 010–255 | Strobe langsam → schnell (30 Hz) |
| 10 | Spot 2 | – | 000–255 | keine Funktion |
| 11 | Spot 3 | Rot | 000–255 | 0–100 % |
| 12 | Spot 3 | Grün | 000–255 | 0–100 % |
| 13 | Spot 3 | Blau | 000–255 | 0–100 % |
| 14 | Spot 3 | Strobe | 000–009 | keine Funktion |
| | | | 010–255 | Strobe langsam → schnell (30 Hz) |
| 15 | Spot 3 | – | 000–255 | keine Funktion |
| 16 | Derby 4 | Rot | 000–255 | 0–100 % |
| 17 | Derby 4 | Grün | 000–255 | 0–100 % |
| 18 | Derby 4 | Blau | 000–255 | 0–100 % |
| 19 | Derby 4 | Strobe | 000–009 | keine Funktion |
| | | | 010–255 | Strobe langsam → schnell (30 Hz) |
| 20 | Derby 4 | Rotation | 000–004 | keine Rotation |
| | | | 005–127 | vorwärts langsam → schnell |
| | | | 128–133 | keine Rotation |
| | | | 134–255 | rückwärts langsam → schnell |
| 21 | Laser | Roter Laser | 000–004 | aus |
| | | | 005–009 | an |
| | | | 010–255 | Strobe langsam → schnell |
| 22 | Laser | Grüner Laser | 000–004 | aus |
| | | | 005–009 | an |
| | | | 010–255 | Strobe langsam → schnell |
| 23 | Laser | Laser-Rotation | 000–004 | keine Rotation |
| | | | 005–127 | vorwärts langsam → schnell |
| | | | 128–133 | keine Rotation |
| | | | 134–255 | rückwärts langsam → schnell |
| 24 | Strobe-LEDs | Weiße LED 1 | 000–004 | aus |
| | | | 005–009 | an |
| | | | 010–255 | Strobe langsam → schnell |
| 25 | Strobe-LEDs | Weiße LED 2 | 000–004 / 005–009 / 010–255 | aus / an / Strobe |
| 26 | Strobe-LEDs | Weiße LED 3 | 000–004 / 005–009 / 010–255 | aus / an / Strobe |
| 27 | Strobe-LEDs | Weiße LED 4 | 000–004 / 005–009 / 010–255 | aus / an / Strobe |
| 28 | UV-LEDs | UV | 000–004 | aus |
| | | | 005–009 | an |
| | | | 010–255 | UV-Strobe langsam → schnell |

Im 28-Kanal-Modus gibt es keinen Master-Dimmer; die Helligkeit läuft über die RGB-Kanäle.

---

## ADJ Inno Pocket Spot – 11-Kanal-Modus

| Kanal | Funktion | Wert | Bedeutung |
|---|---|---|---|
| 1 | Pan | 0–255 | Pan 8 Bit |
| 2 | Pan fein | 0–255 | Pan 16 Bit |
| 3 | Tilt | 0–255 | Tilt 8 Bit |
| 4 | Tilt fein | 0–255 | Tilt 16 Bit |
| 5 | Farbrad | 0–7 | Weiß |
| | | 8–14 | Rot |
| | | 15–21 | Orange |
| | | 22–28 | Gelb |
| | | 29–35 | Grün |
| | | 36–42 | Blau |
| | | 43–49 | Hellblau |
| | | 50–56 | Pink |
| | | 57–127 | Split-Farben |
| | | 128–189 | Farbwechsel schnell → langsam |
| | | 190–193 | Stopp |
| | | 194–255 | Farbwechsel langsam → schnell |
| 6 | Goborad | 0–7 | offen |
| | | 8–15 | Gobo 1 |
| | | 16–23 | Gobo 2 |
| | | 24–31 | Gobo 3 |
| | | 32–39 | Gobo 4 |
| | | 40–47 | Gobo 5 |
| | | 48–55 | Gobo 6 |
| | | 56–63 | Gobo 7 |
| | | 64–71 | offen, Shake |
| | | 72–79 | Gobo 1 Shake |
| | | 80–87 | Gobo 2 Shake |
| | | 88–95 | Gobo 3 Shake |
| | | 96–103 | Gobo 4 Shake |
| | | 104–111 | Gobo 5 Shake |
| | | 112–119 | Gobo 6 Shake |
| | | 120–127 | Gobo 7 Shake |
| | | 128–189 | Gobo-Wechsel schnell → langsam |
| | | 190–193 | Stopp |
| | | 194–255 | Gobo-Wechsel langsam → schnell |
| 7 | Shutter/Strobe | 0–7 | Blackout |
| | | 8–15 | offen |
| | | 16–131 | Strobe langsam → schnell |
| | | 132–139 | offen |
| | | 140–181 | Puls: langsam auf, schnell zu |
| | | 182–189 | offen |
| | | 190–231 | Puls: schnell auf, langsam zu |
| | | 232–239 | offen |
| | | 240–247 | Zufalls-Strobe |
| | | 248–255 | offen |
| 8 | Dimmer | 0–255 | 0–100 % |
| 9 | Bewegungsgeschwindigkeit | 0–255 | schnell → langsam (0 = schnell) |
| 10 | Funktionen | 1–69 | keine Funktion |
| | | 70–79 | Blackout bei Pan/Tilt |
| | | 80–89 | kein Blackout bei Pan/Tilt |
| | | 90–99 | Blackout bei Farbwechsel |
| | | 100–109 | kein Blackout bei Farbwechsel |
| | | 110–119 | Blackout bei Gobowechsel |
| | | 120–129 | kein Blackout bei Gobowechsel |
| | | 130–199 | keine Funktion |
| | | 200–209 | Reset alles |
| | | 210–249 | keine Funktion |
| | | 250–255 | Sound-Modus |
| 11 | Dimmerkurven | 0–41 | Standard |
| | | 42–84 | Stage |
| | | 85–127 | TV |
| | | 128–170 | Architectural |
| | | 171–213 | Theater |
| | | 214–255 | Einstellung am Gerät |

---

## Cameo HYDRABEAM 400 RGBW (CLHB400RGBW) – 56-Kanal-Modus

Handbuch S. 30–31. Der 56-Kanal-Modus braucht Firmware 1.1 oder neuer (S. 39).
Vier gleiche Blöcke mit je 14 Kanälen, ein Block pro Kopf:
Kopf 1 = Kanal 1–14, Kopf 2 = 15–28, Kopf 3 = 29–42, Kopf 4 = 43–56
(Kanal = (Kopf − 1) × 14 + Position im Block).

| Pos. | K1 | K2 | K3 | K4 | Funktion | Wert | Bedeutung |
|---|---|---|---|---|---|---|---|
| 1 | 1 | 15 | 29 | 43 | Pan | 000–255 | |
| 2 | 2 | 16 | 30 | 44 | Pan fein | 000–255 | |
| 3 | 3 | 17 | 31 | 45 | Tilt | 000–255 | |
| 4 | 4 | 18 | 32 | 46 | Tilt fein | 000–255 | |
| 5 | 5 | 19 | 33 | 47 | Kopf-Geschwindigkeit | 000–255 | langsam → schnell |
| 6 | 6 | 20 | 34 | 48 | Dimmer | 000–255 | 0–100 % |
| 7 | 7 | 21 | 35 | 49 | Strobe | 000–010 | kein Strobe |
| | | | | | | 011–255 | langsam → schnell |
| 8 | 8 | 22 | 36 | 50 | Farbe | 000–030 | Farbe über R/G/B/W dieses Kopfes |
| | | | | | | 031–255 | Farb-Makro (Tabelle unten) |
| 9 | 9 | 23 | 37 | 51 | Show / Sound / Reset | 000–007 | keine Funktion |
| | | | | | | 008–030 | Show 1 |
| | | | | | | 031–053 | Show 2 |
| | | | | | | 054–076 | Show 3 |
| | | | | | | 077–099 | Show 4 |
| | | | | | | 100–122 | Sound-Modus |
| | | | | | | 123–199 | keine Funktion |
| | | | | | | 200–224 | Reset |
| | | | | | | 225–255 | keine Funktion |
| 10 | 10 | 24 | 38 | 52 | Sound-Empfindlichkeit / Show-Geschwindigkeit | 000–255 | |
| 11 | 11 | 25 | 39 | 53 | Rot | 000–255 | 0–100 % |
| 12 | 12 | 26 | 40 | 54 | Grün | 000–255 | 0–100 % |
| 13 | 13 | 27 | 41 | 55 | Blau | 000–255 | 0–100 % |
| 14 | 14 | 28 | 42 | 56 | Weiß | 000–255 | 0–100 % |

Farb-Makros (Kanal „Farbe“, Werte aus den 6/10/32-Kanal-Tabellen S. 27–29):

| Wert | Farbe | Wert | Farbe | Wert | Farbe |
|---|---|---|---|---|---|
| 031–045 | R | 106–120 | RB | 181–195 | RGB |
| 046–060 | G | 121–135 | RW | 196–210 | RGW |
| 061–075 | B | 136–150 | GB | 211–225 | RBW |
| 076–090 | W | 151–165 | GW | 226–240 | GBW |
| 091–105 | RG | 166–180 | BW | 241–255 | RGBW |

Hinweise:
- Im Handbuch steht beim Farbkanal „use CH10-CH13“ – Tippfehler, gemeint sind die R/G/B/W-Kanäle des jeweiligen Kopfes (Pos. 11–14).
- Die Open-Fixture-Library-Definition weicht ab: falsche Show-Bereiche (16 Shows statt 4, kein Reset)
  und bei Kopf 2–4 eine umgekehrte Geschwindigkeitsrichtung. Maßgeblich ist das Handbuch.

Andere Modi: 6 Kanäle (Master-Dimmer, Strobe, Shows, Farbe – alle Köpfe gemeinsam),
10 Kanäle (zusätzlich Pan/Tilt gemeinsam), 19 Kanäle (Pan/Tilt/Dimmer je Kopf, RGBW gemeinsam),
32 Kanäle (Pan/Tilt fein, Speed und Farb-Makro je Kopf, RGBW gemeinsam).

---

## Abgleich mit deinen Attribute-Cues (Venue „Default“)

| Cue | Gerät / Attribut | Wert | Bedeutung laut Handbuch |
|---|---|---|---|
| KLS Laser OFF | KLS Rot / Grün / Rotation | 0 / 0 / 0 | aus / aus / keine Rotation ✓ |
| KLS Laser Red Slow | KLS Rot / Grün / Rotation | 9 / 0 / 19 | **Rot an (kein Strobe)** / aus / vorwärts langsam |
| KLS Laser Green Slow | KLS Rot / Grün / Rotation | 0 / 9 / 19 | aus / **Grün an** / vorwärts langsam |
| Derby Slow | Derby 1 + 4 Rotation | 5 | vorwärts, langsamste Stufe ✓ |
| Derby Fast | Derby 1 + 4 Rotation | 224 | **rückwärts**, schnell |
| Derby Stopp | Derby 1 + 4 Rotation | 0 | keine Rotation ✓ |
| Gobo Beam | Inno Gobo | 0 | offen (kein Gobo) |
| Gobo Multi Beam | Inno Gobo | 27 | Gobo 3 |
| Gobo Change auto | Inno Gobo | 28 | **Gobo 3 fest** – kein automatischer Wechsel (der wäre 128–255) |
| Gobo Shake Multi Beam | Inno Gobo | 88 | Gobo 3 Shake ✓ |
| Gobo Rotate | Inno Gobo | 134 | Gobo-Wechsel schnell (der Inno hat keine Gobo-Rotation, nur Rad-Scroll) |
| Gobo S-M Beam | Inno Gobo (Spot 1 / Spot 2) | 21 / 0 | Gobo 2 / offen |
| Hydra Speed Slow | Hydrabeam Kopf-Speed (Gruppe L / Köpfe) | 38 / 31, 31, 224 | langsam / langsam, langsam, **schnell** |
| Hydra Speed Fast | Hydrabeam Kopf-Speed (L, R / Köpfe) | 255 / 17, 255, 24 | schnell / **sehr langsam**, schnell, **sehr langsam** |

Auffällig:
- **„Derby Fast“ dreht rückwärts** (224 liegt im Bereich 134–255). Für vorwärts schnell wäre ~120 nötig.
- **„Gobo Change auto“ wechselt nicht automatisch**, sondern steht fest auf Gobo 3.
- **„KLS Laser … Slow“**: Der Laser ist dauerhaft an, „Slow“ bezieht sich nur auf die Rotation.
- Der zweite Wert im Cue „Gobo Change auto“ (41) liegt auf einem weiteren Inno-Attribut, das ich nicht sicher zuordnen kann.
- **DJ Blazor Slow/Med** sind inzwischen für den neuen Blazor gesetzt. Die interne Attribut-Nummerierung von SoundSwitch
  für den Blazor (8, 84, 85, 256, 257) kann ich noch nicht sicher den Kanälen zuordnen; dafür müsste ich
  einmal sehen, welche Häkchen im Cue-Dialog dazu gehören. Gobo (Nummer 8) ist bei allen Geräten gleich:
  Slow = 186 → Gobo-Wechsel im Uhrzeigersinn, Med = 255 → gegen den Uhrzeigersinn (langsam).
- „DJ Blazor Fast“ und die Blazor-Anteile der Gobo-Cues zeigen noch auf den alten Blazor.
- **Hydra Speed:** Laut Handbuch läuft die Kopf-Geschwindigkeit bei allen Köpfen 0 = langsam → 255 = schnell.
  „Hydra Speed Fast“ setzt einzelne Köpfe aber auf 17 bzw. 24 (= sehr langsam), „Hydra Speed Slow“ einen Kopf auf 224 (= schnell).
  Annahme: SoundSwitch-Attribut 82 ist bei den Hydrabeams die Kopf-Geschwindigkeit (passt zum Cue-Namen). Falls das
  SoundSwitch-Profil die Richtung bei Kopf 2–4 umdreht (wie die fehlerhafte Open-Fixture-Library-Definition), wären die Werte
  beabsichtigt – das zeigt sich am Gerät.

## Quellen

- [Chauvet DJ Blazor User Manual Rev. 3](https://www.chauvetdj.com/wp-content/uploads/2025/01/Blazor_UM_Rev3.pdf)
- [Eurolite LED KLS Laser Bar PRO FX Light Set, Bedienungsanleitung (Art.-Nr. 51741091)](https://gzhls.at/blob/ldb/7/5/1/3/d761b8785e7fffb373137695d1b792a8762d.pdf)
- [ADJ Inno Pocket Spot User Instructions Rev. 3/14](https://d295jznhem2tn9.cloudfront.net/ItemRelatedFiles/6902/inno_pocket_spot.pdf)
- [Cameo HYDRABEAM 400 User Manual (CLHB400W / CLHB400RGBW)](https://www.cameolight.com/en/downloads/file/id/1380290362)
- [Open Fixture Library: Cameo Hydrabeam 400 RGBW](https://open-fixture-library.org/cameo/hydrabeam-400-rgbw) (nur zum Abgleich)
