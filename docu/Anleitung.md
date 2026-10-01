# Venue mit allen Looks kopieren (SoundSwitch 2.11)

SoundSwitch kopiert beim „+“ nur die Geräte einer Venue. Statische Looks, Positionen und
Attribute-Cues (Gobo, Rotation, Laser …) bleiben in der Kopie leer, Geräte-Typ (Wash/Multi Cell,
Primary/Secondary …) und Gruppen-Zuordnung werden zurückgesetzt. Das Skript
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
   Im Geräte-Tab sollten Typ (z. B. „Multi Cell (Primary)“) und Group1–4 wie in der Quelle stehen.
5. **Erst jetzt** in der neuen Venue Geräte entfernen, die du für dieses Setup nicht dabei hast.

`copy` überträgt: Geräte-Typ und Gruppen, Positions-Presets, statische Looks (Slots 1–32) und
Attribute-Cues. Geräte-Farben werden nicht übertragen.

## Wichtig

- Die Ziel-Venue muss eine **unveränderte** Kopie der Quelle sein (gleiche Geräte, gleiche
  Reihenfolge). Sonst bricht das Skript mit einer Meldung ab und schreibt nichts.
- Vorhandene Looks und Cues der Ziel-Venue werden **überschrieben**.
- SoundSwitch muss beim Schreiben geschlossen sein.
- Meldung „verwaiste Verweise in Quelle ignoriert“: Die Quell-Venue enthält noch Werte für
  Geräte, die dort gelöscht oder ausgetauscht wurden. Die haben auch in der Quelle keine
  Wirkung. Beispiel: DJ-Blazor-Cues nach dem Tausch des Blazors am 01.10.2026 – dort die
  Werte in „Default“ neu setzen, dann werden sie beim nächsten Kopieren mitgenommen.

## Geräte-Typ und Gruppen prüfen oder nachtragen

SoundSwitch setzt beim „+“ bei jedem Gerät den Typ auf „Wash (Primary)“ und löscht die
Gruppen. `copy` macht das rückgängig. Für Venues, die schon einen anderen Gerätebestand haben
(Geräte entfernt), gibt es `flags` – es überträgt nur Typ und Gruppen und lässt alles andere stehen.
Geräte werden über Profil, Kanalmodus und DMX-Adresse zugeordnet, die Reihenfolge ist egal.

```bash
# Geräte einer Venue mit Typ und Gruppen anzeigen
python3 specs/ssvenues.py fixtures ~/Music/SoundSwitch/DJ_eMPi.ssproj/SoundSwitchVenues.bin "KLS-PT"

# Typ und Gruppen aus Default nachtragen (ohne --write nur Anzeige)
python3 specs/ssvenues.py flags ~/Music/SoundSwitch/DJ_eMPi.ssproj/SoundSwitchVenues.bin "Default" "KLS-PT" --write
```

Bekannte Typ-Werte: 2 Wash (Primary), 3 Wash (Secondary), 4 Wash (Tertiary),
11 Multi Cell (Primary), 12 Multi Cell (Secondary). Andere Werte (Hazer, KLS, Thunderwash)
zeigt `fixtures` als Zahl, sie werden unverändert mitkopiert.

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
- Gerät alternativ als `"#Nummer"` (Knoten-Nummer im Gerätebaum) angeben, nötig bei gleichnamigen
  Geräten wie den Inno Spots oder Hydrabeam-Köpfen. Attribut alternativ als Zahl (SoundSwitch-
  Attributnummer), sicherer bei Geräten mit mehreren Kanalmodi. Die Knoten-Nummern sind je Venue
  verschieden.

### Alle Cue-Werte auf einmal: `specs/cues_setzen.sh`

Das Skript setzt die am 01.10.2026 getesteten Werte (Blazor-Gobos, Inno-Gobo-Rad, KLS-Derbys,
Hydrabeam-Speed) für eine Venue. Die Knoten-Nummern sind darin pro Venue hinterlegt
(„Test-Kopie“, „Default“); für eine weitere Venue dort einen Eintrag ergänzen.

```bash
bash specs/cues_setzen.sh ~/Music/SoundSwitch/DJ_eMPi.ssproj/SoundSwitchVenues.bin "Default"          # Trockenlauf
bash specs/cues_setzen.sh ~/Music/SoundSwitch/DJ_eMPi.ssproj/SoundSwitchVenues.bin "Default" --write
```

## Zurück zum alten Stand

Jeder `--write`-Lauf legt neben der Datei ein Backup an:
`SoundSwitchVenues.bin.JJJJ-MM-TT_HHMMSS.bak`. Das Cue-Skript erzeugt pro Aufruf ein Backup,
also viele; alte `.bak`-Dateien können gelöscht werden.

SoundSwitch beenden, die aktuelle `SoundSwitchVenues.bin` löschen oder umbenennen, das
Backup in `SoundSwitchVenues.bin` umbenennen.

## Getestet

- 01.10.2026: „Default“ → „Test-Kopie“. Statische Looks, Positionen und Attribute-Cues
  in SoundSwitch geprüft, funktionieren.
- 01.10.2026: Attribute-Cues (Blazor, Inno, KLS-Derbys, Hydrabeam) in „Test-Kopie“ getestet und
  mit `cues_setzen.sh` in „Default“ übernommen.
- 01.10.2026: Typ/Gruppen-Verlust beim „+“ gefunden (Beleg: unberührte SoundSwitch-Kopie hatte
  überall „Wash (Primary)“, Gruppe 0). Mit `flags` aus „Default“ nachgetragen in Basic-CBL-PT,
  Basic-CBL, Basic-CBL-PT-Hy, KLS-PT-Hy, KLS-PT; „Test Kopie“ per `copy`.
