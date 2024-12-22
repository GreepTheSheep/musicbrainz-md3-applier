import os
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
import musicbrainzngs
import eyed3

# Configurer l'API MusicBrainz
musicbrainzngs.set_useragent("AlbumMetadataScript", "1.0", "contact@example.com")

def get_album_metadata(musicbrainz_url):
    """Récupère les métadonnées d'un album à partir d'un lien MusicBrainz."""
    try:
        release_id = musicbrainz_url.split('/')[-1]
        release = musicbrainzngs.get_release_by_id(release_id, includes=["recordings", "media"])
        album_data = release["release"]

        # Récupérer les informations des pistes
        tracks = []
        for medium in album_data.get("medium-list", []):
            side = medium.get("title", "")
            for track in medium.get("track-list", []):
                track_number = track.get("position", "")
                if side:
                    track_number = f"{side} {track_number}"

                # Débogage : afficher le contenu brut de artist-credit
                artist_credit = track["recording"].get("artist-credit", [])
                print(f"artist-credit brut pour la piste {track.get('position', 'inconnue')}: {artist_credit}")

                if artist_credit:
                    artist = " ".join([credit.get("artist", {}).get("name", "Artiste inconnu") for credit in artist_credit if "artist" in credit])
                else:
                    # Utiliser "artist" à un autre niveau si "artist-credit" est vide
                    artist = track["recording"].get("artist", {}).get("name", None)
                    if not artist:
                        artist = input(f"Nom de l'artiste introuvable pour la piste {track_number}. Veuillez entrer le nom de l'artiste : ")

                title = track["recording"].get("title", None)
                if not title:
                    title = input(f"Titre introuvable pour la piste {track_number}. Veuillez entrer le titre : ")

                tracks.append({
                    "number": track_number,
                    "title": title,
                    "artist": artist
                })

        album_artist_credit = album_data.get("artist-credit", [])
        print(f"artist-credit brut pour l'album : {album_artist_credit}")
        album_artist = " ".join([credit.get("artist", {}).get("name", "Artiste inconnu") for credit in album_artist_credit if "artist" in credit])

        return {
            "title": album_data.get("title", "Album inconnu"),
            "artist": album_artist or "Artiste inconnu",
            "tracks": tracks
        }
    except Exception as e:
        print(f"Erreur lors de la récupération des métadonnées : {e}")
        return None

def apply_metadata_to_mp3(directory, album_metadata, cover_image):
    """Applique les métadonnées aux fichiers MP3 dans le dossier spécifié."""
    mp3_files = sorted([f for f in os.listdir(directory) if f.endswith(".mp3")])

    if len(mp3_files) != len(album_metadata["tracks"]):
        print("Le nombre de fichiers MP3 ne correspond pas au nombre de pistes dans les métadonnées.")
        return

    for mp3_file, track in zip(mp3_files, album_metadata["tracks"]):
        file_path = os.path.join(directory, mp3_file)
        try:
            audio = MP3(file_path, ID3=EasyID3)
            audio["title"] = track["title"]
            audio["artist"] = track["artist"]
            audio["album"] = album_metadata["title"]
            audio["tracknumber"] = track["number"]
            audio.save()
            print(f"Métadonnées appliquées à {mp3_file} : Titre - {track['title']}, Artiste - {track['artist']}")
            ajouter_couverture_mp3(file_path, cover_image)
        except Exception as e:
            print(f"Erreur lors de l'application des métadonnées à {mp3_file} : {e}")

def ajouter_couverture_mp3(mp3_file, cover_image):
    # Charger le fichier MP3
    audio_file = eyed3.load(mp3_file)

    # Ouvrir l'image de couverture
    with open(cover_image, "rb") as img_file:
        cover_data = img_file.read()

    # Ajouter la couverture au fichier MP3
    audio_file.tag.images.set(3, cover_data, "image/jpeg", u"cover")

    # Sauvegarder les modifications
    audio_file.tag.save()
    print(f"Couverture ajoutée avec succès à {mp3_file}")

if __name__ == "__main__":
    musicbrainz_url = input("Entrez le lien de la parution MusicBrainz : ")
    directory = input("Entrez le chemin du dossier contenant les fichiers MP3 : ")
    cover_image = input("Entrez le chemin du fichier contenant la couverture album : ")

    album_metadata = get_album_metadata(musicbrainz_url)
    if album_metadata:
        apply_metadata_to_mp3(directory, album_metadata, cover_image)
        print("\nMétadonnées appliquées avec succès !")
    else:
        print("Impossible de récupérer les métadonnées de l'album.")
