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

# Nom du fichier NFO
NFO_FILE="${DIR%/}.nfo"

# Générer le contenu du fichier NFO
echo "Génération du fichier NFO pour le dossier : $DIR"

# Lister les fichiers en ordre alphabétique et obtenir leurs informations
find "$DIR" -type f | sort | while read file; do
    # Obtenir seulement le nom du fichier
    filename=$(basename "$file")
    echo "General" >> "$NFO_FILE"
    echo "Complete name                            : $filename" >> "$NFO_FILE"
    mediainfo "$file" | grep -E "Format                                   :|File size                                :|Duration                                 :|Overall bit rate mode                    :|Overall bit rate                         :|Album                                    :|Album/Performer                          :|Track name                               :|Track name/Position                      :|Performer                                :|Composer                                 :|Lyricist                                 :|Genre                                    :|Recorded date                            :|Copyright                                :|Cover                                    :|Cover type                               :|Cover MIME                               :|ARRANGER                                 :" >> "$NFO_FILE"
    echo "" >> "$NFO_FILE"
    echo "Audio" >> "$NFO_FILE"
    mediainfo "$file" | grep -E "Format                                   :|Format version                           :|Format profile                           :|Format settings                          :|Duration                                 :|Bit rate mode                            :|Bit rate                                 :|Channel\(s\)                              :|Sampling rate                            :|Frame rate                               :|Compression mode                         :|Stream size                              :" >> "$NFO_FILE"
    echo "" >> "$NFO_FILE"
done

echo "Fichier NFO généré : $NFO_FILE"
