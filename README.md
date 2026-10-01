# SoundSwitch Venue Tools

Werkzeuge rund um die `SoundSwitchVenues.bin` von SoundSwitch 2.11 (reverse engineered).

SoundSwitch kopiert beim „+“ nur die Geräte einer Venue. Statische Looks, Positionen und
Attribute-Cues bleiben in der Kopie leer, Geräte-Typ und Gruppen werden zurückgesetzt. `specs/ssvenues.py` überträgt sie nachträglich
und kann einzelne Attribut-Werte in Cues setzen.

## Inhalt

- `specs/ssvenues.py` – Parser und Kopierwerkzeug (`info`, `fixtures`, `copy`, `flags`, `set`)
- `specs/cues_setzen.sh` – Beispielskript, das Attribute-Cues per `set` befüllt
- `docu/Anleitung.md` – Schritt-für-Schritt-Anleitung
- `docu/format.md` – Beschreibung des Binärformats
- `docu/DMX-Kanaele.md` – DMX-Kanalbelegung der verwendeten Geräte

## Schnellstart

```bash
python3 specs/ssvenues.py info  <SoundSwitchVenues.bin>
python3 specs/ssvenues.py fixtures <SoundSwitchVenues.bin> "<Venue>"
python3 specs/ssvenues.py copy  <SoundSwitchVenues.bin> "<Quell-Venue>" "<Ziel-Venue>" --write
python3 specs/ssvenues.py flags <SoundSwitchVenues.bin> "<Quell-Venue>" "<Ziel-Venue>" --write   # nur Typ/Gruppen
python3 specs/ssvenues.py set   <SoundSwitchVenues.bin> "<Venue>" "<Cue>" "<Gerät>" "Attribut=Wert" --write
```

Ohne `--write` wird nur simuliert. Vor dem Schreiben wird eine Sicherungskopie angelegt.
SoundSwitch muss während des Schreibens geschlossen sein.
