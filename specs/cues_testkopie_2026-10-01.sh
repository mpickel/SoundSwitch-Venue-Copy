#!/bin/bash
# Attribute-Cues in "Test-Kopie" nach Handbuch-Werten setzen (docu/DMX-Kanaele.md).
# Aufruf: specs/cues_testkopie_2026-10-01.sh <SoundSwitchVenues.bin> [--write]
# Attribut-Nummern: Inno Gobo = 8, Inno Funktionen = 88, KLS Derby-Rotation = 82, Hydra Kopf-Speed = 82.
# KLS-Laser bleibt aus (Cue "KLS Laser OFF" unverändert, kein Cue schaltet ihn ein).
set -e
F="$1"; W="$2"; V="Test-Kopie"
SS="python3 $(dirname "$0")/ssvenues.py set"

# Gobo-Cues: Blazor ergänzen
$SS "$F" $V "Gobo Beam"             Blazor "Gobo=10" "Gobo Rotation=60"  $W
$SS "$F" $V "Gobo Multi Beam"       Blazor "Gobo=50" "Gobo Rotation=60"  $W
$SS "$F" $V "Gobo Shake Multi Beam" Blazor "Gobo=50" "Gobo Rotation=235" $W
$SS "$F" $V "Gobo Rotate"           Blazor "Gobo=50" "Gobo Rotation=110" $W
$SS "$F" $V "Gobo Change auto"      Blazor "Gobo=170"                    $W

# Inno: Rad dreht (Gobo Rotate) bzw. wechselt automatisch (Gobo Change auto, Funktionen 41 bleibt)
for N in "#9" "#10"; do
  $SS "$F" $V "Gobo Rotate"      "$N" "8=160"          $W
  $SS "$F" $V "Gobo Change auto" "$N" "8=160" "88=41"  $W
done

# KLS Derbys (Derby 1 = #12, Derby 4 = #15)
for N in "#12" "#15"; do
  $SS "$F" $V "Derby Slow" "$N" "82=20"  $W
  $SS "$F" $V "Derby Fast" "$N" "82=120" $W
done

# Hydrabeam: alle 8 Köpfe einheitlich
for N in "#22" "#23" "#24" "#25" "#27" "#28" "#29" "#30"; do
  $SS "$F" $V "Hydra Speed Slow" "$N" "82=40"  $W
  $SS "$F" $V "Hydra Speed Fast" "$N" "82=255" $W
done
