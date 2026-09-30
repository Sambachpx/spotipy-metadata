"""Extraction locale des métadonnées d'un fichier audio (mutagen)."""

import mutagen


def extract_metadata(file_path: str) -> tuple[str, int]:
    """Retourne (titre, durée en secondes) d'un fichier audio.

    Lève ValueError si le fichier est illisible ou sans piste audio.
    """
    metadata = mutagen.File(file_path)
    if metadata is None or metadata.info is None:
        raise ValueError(f"Unsupported or unreadable audio file: {file_path}")

    duration = int(metadata.info.length)

    name = ""
    if "TIT2" in metadata:
        title = metadata["TIT2"].text[0]
        name = str(title)

    return name, duration
