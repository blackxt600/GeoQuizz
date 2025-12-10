"""
Module de gestion des photos et extraction des métadonnées EXIF
"""
import os
import random
from pathlib import Path
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS


class PhotoManager:
    def __init__(self, root_folder):
        """
        Initialise le gestionnaire de photos

        Args:
            root_folder: Chemin du dossier racine contenant les photos
        """
        self.root_folder = Path(root_folder)
        self.photos_with_gps = []

    def scan_photos(self):
        """
        Parcourt récursivement le dossier racine pour trouver toutes les photos
        avec des coordonnées GPS dans leurs métadonnées EXIF
        """
        self.photos_with_gps = []

        # Extensions d'images supportées
        image_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.bmp'}

        # Parcourir tous les fichiers
        for file_path in self.root_folder.rglob('*'):
            if file_path.suffix.lower() in image_extensions:
                coords = self._extract_gps_coordinates(file_path)
                if coords:
                    self.photos_with_gps.append({
                        'path': str(file_path),
                        'latitude': coords['latitude'],
                        'longitude': coords['longitude']
                    })

        return len(self.photos_with_gps)

    def _extract_gps_coordinates(self, image_path):
        """
        Extrait les coordonnées GPS des métadonnées EXIF d'une image

        Args:
            image_path: Chemin vers l'image

        Returns:
            Dict avec latitude et longitude, ou None si pas de GPS
        """
        try:
            image = Image.open(image_path)
            exif_data = image._getexif()

            if not exif_data:
                return None

            # Chercher les données GPS
            gps_info = None
            for tag, value in exif_data.items():
                tag_name = TAGS.get(tag, tag)
                if tag_name == 'GPSInfo':
                    gps_info = value
                    break

            if not gps_info:
                return None

            # Extraire latitude et longitude
            gps_data = {}
            for key, value in gps_info.items():
                tag_name = GPSTAGS.get(key, key)
                gps_data[tag_name] = value

            # Convertir les coordonnées
            lat = self._convert_to_degrees(gps_data.get('GPSLatitude'))
            lon = self._convert_to_degrees(gps_data.get('GPSLongitude'))

            if lat is None or lon is None:
                return None

            # Appliquer les références (N/S, E/W)
            if gps_data.get('GPSLatitudeRef') == 'S':
                lat = -lat
            if gps_data.get('GPSLongitudeRef') == 'W':
                lon = -lon

            return {
                'latitude': lat,
                'longitude': lon
            }

        except Exception as e:
            return None

    def _convert_to_degrees(self, value):
        """
        Convertit les coordonnées GPS du format EXIF en degrés décimaux

        Args:
            value: Tuple de coordonnées (degrés, minutes, secondes)

        Returns:
            Coordonnée en degrés décimaux
        """
        if not value:
            return None

        try:
            d = float(value[0])
            m = float(value[1])
            s = float(value[2])

            return d + (m / 60.0) + (s / 3600.0)
        except:
            return None

    def get_random_photo(self):
        """
        Retourne une photo aléatoire parmi celles ayant des coordonnées GPS

        Returns:
            Dict avec les informations de la photo, ou None si aucune photo disponible
        """
        if not self.photos_with_gps:
            return None

        return random.choice(self.photos_with_gps)

    def get_random_photos(self, count):
        """
        Retourne plusieurs photos aléatoires

        Args:
            count: Nombre de photos à retourner

        Returns:
            Liste de photos
        """
        if not self.photos_with_gps:
            return []

        # Si on demande plus de photos qu'il n'y en a, retourner toutes les photos
        if count >= len(self.photos_with_gps):
            photos = self.photos_with_gps.copy()
            random.shuffle(photos)
            return photos

        return random.sample(self.photos_with_gps, count)
