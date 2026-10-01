# Dateiformat `SoundSwitchVenues.bin` (SoundSwitch 2.11)

Selbst entschlüsselt, nicht offiziell dokumentiert. Alle Zahlen Little-Endian `u32`,
Texte als `u32 Zeichenzahl inkl. Null` + UTF-16LE. GUIDs 16 Bytes roh.

## Abschnitte in Dateireihenfolge

| Abschnitt | Inhalt |
|---|---|
| Header | `aaaa0955`, `3`, `offA`, `offB`, `?`, Anzahl Venues. `offA` zeigt auf den Tail, `offB = offA + 30`. |
| Venues | je Venue ein Block ab `04000000 GUID 01000000 Name 0f000000 …` |
| Positionen | `02000000 00000000`, dann je Preset: `02000000`, n Venue-Einträge (`GUID 02000000 n × (Knoten, 1, 8 Bytes)`), `01000000 Name GUID Farbe a`; danach Reihenfolge-Liste und 14 Bytes |
| Statische Looks 1–32 | `u32 Anzahl`, je Schlüssel: `GUID 01000000 20000000` + 32 Slots |
| Attribute-Cues | `02000000 00000000`, dann je Cue: `01000000`, n Venue-Einträge (`GUID 01 01 n × (1, Knoten, Attribut, Wert)`), `01000000 Name GUID Farbe a`; danach Reihenfolge-Liste |
| Cue-Gruppen | Ordner wie „DJ Blazor“, „KLS“, „Hydra“ (nicht weiter entschlüsselt, wird unverändert übernommen) |
| Looks 33–128 | `u32 Anzahl`, je Schlüssel: `GUID 02000000` + 96 Slots + 128 × 25 Bytes (Typ 6) |
| Geräte-Datensatz-Ende | jeder oberste Geräte-Datensatz endet mit `Profil-GUID` + 6 × u32: `hash, Modus, DMX-Adresse−1, Profil-Hash, Typ, Gruppen`. Typ: 2 Wash (Primary), 3 Wash (Secondary), 4 Wash (Tertiary), 11 Multi Cell (Primary), 12 Multi Cell (Secondary), andere Werte unbekannt. Gruppen: Group1–4, 0 = keine. SoundSwitch setzt beide beim „+“-Kopieren zurück; `copy` überträgt sie per (GUID, Modus, DMX) |
| Tail | 46 Bytes, Tabelle `(Offset, Länge, 0, 1)` je Geräte-Datensatz, `ffffffff`, `u32 7`, `"Default"` |

Look-Slot: `05000000 01000000 Name`, dann 5 Listen: A `Index + double` (12 B),
B (12 B), C (12 B), D `Index + GUID` (20 B, Positions-Preset), E (16 B).

## Geräte-Nummern

Positionen und Attribute-Cues verweisen auf **Knoten des Geräte-Baums der jeweiligen
Venue**. Knoten: `03000000 02000000 <Knoten-ID> 01000000 <Name> …`. Der Baum steht im
Venue-Block **hinter** den Geräte-Datensätzen (davor stehen Geräteprofile mit ähnlich
aussehenden Kanal-Einträgen, die nicht dazugehören).

SoundSwitch vergibt beim Kopieren einer Venue neue, lückenlose Knoten-IDs. Deshalb reicht
es nicht, Einträge nur mit der neuen Venue-GUID zu versehen: Die Knoten-IDs müssen über
Namen und Reihenfolge im Baum von der Quelle auf die Kopie umgerechnet werden.

Statische Looks (Slots) verwenden in den Listen A–D ein **zweites Nummernsystem**: die
Look-Nummer, die im Baum direkt hinter dem Gerätenamen steht (`<Name> <Look-Nr> <Farbe ARGB> …`,
nur bei Geräten und Zellen; Gruppen-Knoten haben keine). Auch diese Nummern vergibt SoundSwitch
beim Kopieren neu (z. B. L-Maxi 02 L1: Default 32 → KLS-PT 30). Liste E eines Slots verwendet
wie die Attribute-Cues die Knoten-ID (`1, Knoten, Attribut, Wert`).

Beim Kopieren werden beide Nummern über die Gerätenamen in Baum-Reihenfolge zugeordnet
(längste gemeinsame Teilfolge). Geräte, die es nur in einer der beiden Venues gibt, bleiben
ohne Zuordnung; ihre Werte entfallen bzw. bleiben leer. Bis 01.10.2026 wurden Look-Slots roh
kopiert, wodurch Werte in Kopien auf falschen Geräten landeten.

## Bestätigt durch Vergleich

- Inno Pocket Spot (DMX 1): Default Knoten 19 → Test-Kopie 9
- LED KLS Laser Bar Pro, MASTER: Default 33 → Test-Kopie 16
