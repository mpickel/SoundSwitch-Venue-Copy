# Venue mit allen Looks kopieren (SoundSwitch 2.11)

SoundSwitch kopiert beim „+“ nur die Geräte einer Venue. Statische Looks, Positionen und
Attribute-Cues (Gobo, Rotation, Laser …) bleiben in der Kopie leer. Das Skript
`specs/ssvenues.py` überträgt sie nachträglich.

## Ablauf

1. **In SoundSwitch** die Quell-Venue über „+“ kopieren und der Kopie einen Namen geben.
   An den Geräten der Kopie noch nichts ändern.
2. Speichern (Diskette) und **SoundSwitch beenden**.
3. Im Terminal, im Ordner `DJ-Stuff/SoundSwitch`:

   ```bash
   # Übersicht: Venues, belegte Looks, Cues
   python3 specs/ssvenues.py info ~/Music/SoundSwitch/DJ_eMPi.ssproj/SoundSwitchVenues.bin

   # Trockenlauf – zeigt, was übertragen würde, schreibt nichts
   python3 specs/ssvenues.py copy ~/Music/SoundSwitch/DJ_eMPi.ssproj/SoundSwitchVenues.bin "Default" "Neue Venue"

   # Wirklich schreiben (legt vorher automatisch ein Backup an)
   python3 specs/ssvenues.py copy ~/Music/SoundSwitch/DJ_eMPi.ssproj/SoundSwitchVenues.bin "Default" "Neue Venue" --write
   ```

4. SoundSwitch starten, in der neuen Venue ein paar Looks, Positionen und Cues prüfen.
5. **Erst jetzt** in der neuen Venue Geräte entfernen, die du für dieses Setup nicht dabei hast.

## Wichtig

- Die Ziel-Venue muss eine **unveränderte** Kopie der Quelle sein (gleiche Geräte, gleiche
  Reihenfolge). Sonst bricht das Skript mit einer Meldung ab und schreibt nichts.
- Vorhandene Looks und Cues der Ziel-Venue werden **überschrieben**.
- SoundSwitch muss beim Schreiben geschlossen sein.
- Meldung „verwaiste Verweise in Quelle ignoriert“: Die Quell-Venue enthält noch Werte für
  Geräte, die dort gelöscht oder ausgetauscht wurden. Die haben auch in der Quelle keine
  Wirkung. Beispiel: DJ-Blazor-Cues nach dem Tausch des Blazors am 01.10.2026 – dort die
  Werte in „Default“ neu setzen, dann werden sie beim nächsten Kopieren mitgenommen.

## Attribute-Cue-Werte setzen

```bash
python3 specs/ssvenues.py set ~/Music/SoundSwitch/DJ_eMPi.ssproj/SoundSwitchVenues.bin \
  "Test-Kopie" "DJ Blazor Slow" "Blazor" "Gobo=195" "Gobo Rotation=90" --write
```

- Attributnamen wie im Geräteprofil (z. B. Blazor: Gobo, Gobo Rotation, Mirror Rotation,
  Barrel Rotation, Barrel Pan, Auto Program, Auto Speed, Control). Ein falscher Name zeigt die Liste.
- Werte sind DMX-Werte 0–255, Bedeutung siehe `docu/DMX-Kanaele.md`.
- Die bisherigen Werte dieses Geräts im Cue werden ersetzt; andere Geräte im Cue bleiben.
- Ohne `--write` nur Anzeige (alter Wert → neuer Wert).

## Zurück zum alten Stand

Jeder `--write`-Lauf legt neben der Datei ein Backup an:
`SoundSwitchVenues.bin.JJJJ-MM-TT_HHMMSS.bak`

SoundSwitch beenden, die aktuelle `SoundSwitchVenues.bin` löschen oder umbenennen, das
Backup in `SoundSwitchVenues.bin` umbenennen.

## Getestet

- 01.10.2026: „Default“ → „Test-Kopie“. Statische Looks, Positionen und Attribute-Cues
  in SoundSwitch geprüft, funktionieren.
