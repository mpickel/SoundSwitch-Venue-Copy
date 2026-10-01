#!/bin/bash
# Attribute-Cues einer Venue nach Handbuch-Werten setzen (docu/DMX-Kanaele.md).
# Aufruf: specs/cues_setzen.sh <SoundSwitchVenues.bin> "<Venue>" [--write]
# Getestet in "Test-Kopie" am 2026-10-01, danach in "Default" übernommen.
# Attribut-Nummern: Inno Gobo = 8, Inno Funktionen = 88, KLS Derby-Rotation = 82, Hydra Kopf-Speed = 82.
# KLS-Laser bleibt aus (Cue "KLS Laser OFF" unverändert, kein Cue schaltet ihn ein).
# Geräte-Knoten-Nummern sind je Venue verschieden (siehe `ssvenues.py info` bzw. tree_nodes), daher pro Venue hinterlegt.
set -e
F="$1"; V="$2"; W="$3"
SS="python3 $(dirname "$0")/ssvenues.py set"

case "$V" in
  "Test-Kopie")
    INNO="#9 #10"; DERBY="#12 #15"
    HYDRA="#22 #23 #24 #25 #27 #28 #29 #30" ;;
  "Default")
    INNO="#19 #20"; DERBY="#29 #32"
    HYDRA="#73 #74 #75 #76 #79 #80 #81 #82" ;;
  *) echo "Keine Knoten-Nummern für Venue '$V' hinterlegt."; exit 1 ;;
esac

# Gobo-Cues: Blazor ergänzen
$SS "$F" "$V" "Gobo Beam"             Blazor "Gobo=10" "Gobo Rotation=60"  $W
$SS "$F" "$V" "Gobo Multi Beam"       Blazor "Gobo=50" "Gobo Rotation=60"  $W
$SS "$F" "$V" "Gobo Shake Multi Beam" Blazor "Gobo=50" "Gobo Rotation=235" $W
$SS "$F" "$V" "Gobo Rotate"           Blazor "Gobo=50" "Gobo Rotation=110" $W
$SS "$F" "$V" "Gobo Change auto"      Blazor "Gobo=170"                    $W

# Inno: Rad dreht (Gobo Rotate) bzw. wechselt automatisch (Gobo Change auto, Funktionen 41 bleibt)
for N in $INNO; do
  $SS "$F" "$V" "Gobo Rotate"      "$N" "8=160"          $W
  $SS "$F" "$V" "Gobo Change auto" "$N" "8=160" "88=41"  $W
done

# KLS Derbys (Derby 1, Derby 4)
for N in $DERBY; do
  $SS "$F" "$V" "Derby Slow" "$N" "82=20"  $W
  $SS "$F" "$V" "Derby Fast" "$N" "82=120" $W
done

# Hydrabeam: alle 8 Köpfe einheitlich
for N in $HYDRA; do
  $SS "$F" "$V" "Hydra Speed Slow" "$N" "82=40"  $W
  $SS "$F" "$V" "Hydra Speed Fast" "$N" "82=255" $W
done
