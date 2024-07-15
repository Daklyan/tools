#!/bin/bash

# Vérifier que le dossier est spécifié
if [ -z "$1" ]; then
    echo "Usage: $0 chemin_du_dossier"
    exit 1
fi

# Chemin du dossier
DIR="$1"

# Vérifier que le chemin est un dossier valide
if [ ! -d "$DIR" ]; then
    echo "Le chemin spécifié n'est pas un dossier valide."
    exit 1
fi

for file in "$DIR"; do
    mediainfo "$file" --Output="General;[%Track/Position%]. [%Track%] | [%Duration/String%]\n"
done
