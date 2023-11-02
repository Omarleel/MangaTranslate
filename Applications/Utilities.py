import re
import sys
import os
import time
import subprocess
import platform
from zipfile import ZipFile
import requests
sys.path.append(os.path.dirname(os.getcwd()))
from Utils.Constantes import RUTA_ACTUAL, RUTA_FUENTE, RUTA_LOCAL_FUENTES, RUTA_LOCAL_MODELO_INPAINTING, RUTA_LOCAL_TEMPORAL, RUTA_MODELO_LAMA, URL_FUENTE, URL_MODELO_LAMA

import threading
from PIL import Image
from deep_translator import GoogleTranslator
from deep_translator.exceptions import TranslationNotFound
import gdown


class Utilities:
    def __init__(self):
        self.canvas_pdf = None
        self.translator = GoogleTranslator()

    def obtener_abreviacion_idioma(self, idioma_entrada, idioma_salida):
        mapeo_idiomas_admitidos = {
            "Español": "es",
            "Inglés": "en",
            "Portugués": "pt",
            "Francés": "fr",
            "Italiano": "it",
            "Japonés": "ja",
            "Koreano": "ko",
            "Chino": "zh-CN"
        }
        return mapeo_idiomas_admitidos.get(idioma_entrada, "auto"), mapeo_idiomas_admitidos.get(idioma_salida, "es")

    def traducir_texto(self, texto, idioma_entrada, idioma_salida):
        abv_idioma_entrada, abv_idioma_salida = self.obtener_abreviacion_idioma(idioma_entrada, idioma_salida)
        try:
            translator = GoogleTranslator(source=abv_idioma_entrada, target=abv_idioma_salida)
            texto_traducido = translator.translate(texto)
            return texto_traducido
        except TranslationNotFound as e:
            # Maneja el error TranslationNotFound aquí
            print(f"No se pudo encontrar una traducción para el texto: {str(e)}")
            return ""

    def descargar_pdf(self, ruta_pdf_resultante):
        if ruta_pdf_resultante is not None:
            hilo_descarga = threading.Thread(target=self.realizar_descarga_pdf, args=(ruta_pdf_resultante,))
            hilo_descarga.start()
            
    def abrir_pdf(self, ruta_pdf_resultante):
        try:
            if platform.system() == "Windows":
                subprocess.Popen([ruta_pdf_resultante], shell=True)
            elif platform.system() == "Darwin":  # macOS
                subprocess.Popen(["open", ruta_pdf_resultante])
            else:  # Linux
                subprocess.Popen(["xdg-open", ruta_pdf_resultante])
        except Exception as e:
            print(f"Error al abrir el archivo PDF: {e}")

    def realizar_descarga_pdf(self, ruta_pdf_resultante):
        try:
            from google.colab import files
            files.download(ruta_pdf_resultante)
        except Exception as e:
            print(f"Error al descargar el archivo: {e}")

    def capitalizar_oraciones(self, texto):
        oraciones = [s.strip().capitalize() for s in texto.replace('\n', ' ').split('. ') if s]
        return ' '.join(oraciones)

    def generar_pdf(self, imagen_actual, canvas_pdf, ruta_imagen_resultante):
        self.canvas_pdf = canvas_pdf
        img = Image.open(ruta_imagen_resultante)

        img_aspect_ratio = img.width / img.height
        page_width, page_height = self.canvas_pdf._pagesize

        if img_aspect_ratio > 1:
            new_img_width = page_width
            new_img_height = int(page_width / img_aspect_ratio)
        else:
            new_img_height = page_height
            new_img_width = int(page_height * img_aspect_ratio)

        img = img.resize((int(new_img_width), int(new_img_height)), Image.LANCZOS)
        
        timestamp = int(time.time())
        temp_img_path = os.path.join(RUTA_LOCAL_TEMPORAL, f"temp_image_{imagen_actual}_{timestamp}.jpg")
        img.save(temp_img_path, format='JPEG', quality=80)

        self.canvas_pdf.drawImage(temp_img_path, 0, 0, width=int(new_img_width), height=int(new_img_height))
        self.canvas_pdf.showPage()

        os.remove(temp_img_path)
        
    def guardar_pdf(self):
        # Guardar el PDF
        self.canvas_pdf.save()
        
    def download_font_colab(self, drive_manager):
        os.makedirs(RUTA_LOCAL_FUENTES, exist_ok=True)
        drive_manager.download_folder_by_link(URL_FUENTE, RUTA_LOCAL_FUENTES)
    
    def download_lama_model_colab(self, drive_manager):
        os.makedirs(RUTA_LOCAL_MODELO_INPAINTING, exist_ok=True)
        drive_manager.download_folder_by_link(URL_MODELO_LAMA, RUTA_LOCAL_MODELO_INPAINTING)
    
    def convert_gdrive_url_to_gdown(self, original_url):
        # Extrae el ID del archivo usando una expresión regular
        file_id = re.search(r"/file/d/([a-zA-Z0-9_-]+)/view", original_url)
        if file_id:
            return f"https://drive.google.com/uc?id={file_id.group(1)}"
        return None
    
    def download_font_windows(self):
        if not os.path.isfile(RUTA_FUENTE):
            os.makedirs(RUTA_LOCAL_FUENTES, exist_ok=True)
            gdown.download(self.convert_gdrive_url_to_gdown(URL_FUENTE), RUTA_FUENTE, quiet=False)
    
    def download_lama_model_windows(self):
        if not os.path.isfile(RUTA_MODELO_LAMA):
            os.makedirs(RUTA_LOCAL_MODELO_INPAINTING, exist_ok=True)
            gdown.download(self.convert_gdrive_url_to_gdown(URL_MODELO_LAMA), RUTA_MODELO_LAMA, quiet=False)
    
    def get_gdrive_filename(self, file_id):
        url = f"https://drive.google.com/uc?export=download&id={file_id}"
        response = requests.get(url, stream=True) # Usamos stream=True para evitar descargar el archivo
        
        if 'Content-Disposition' in response.headers:
            # Extrayendo el nombre del archivo usando expresiones regulares
            filename = re.findall("filename=\"([^\"]+)", response.headers['Content-Disposition'])
            if filename:
                return filename[0]
        return None
    
    def get_drive_file_id(self, url_drive):
        match = re.search(r"/d/([^/]+)", url_drive)
        if match:
            file_id = match.group(1)
            return file_id
        else:
            return None

    def descargar_y_extraer_zip(self, url_drive):
        try:
            id_archivo = self.get_drive_file_id(url_drive)
            nombre_archivo = self.get_gdrive_filename(id_archivo).replace(".zip", "")
            ruta_destino = f"{RUTA_ACTUAL}/{nombre_archivo}"
            os.makedirs(ruta_destino, exist_ok=True)
            url_gdown = f'https://drive.google.com/uc?id={id_archivo}'
            ruta_archivo_descargado = f"{ruta_destino}/{nombre_archivo}.zip"
            gdown.download(url_gdown, ruta_archivo_descargado, quiet=False)
            with ZipFile(ruta_archivo_descargado, "r") as zip_ref:
                zip_ref.extractall(ruta_destino)
            os.remove(ruta_archivo_descargado)
            return ruta_destino.replace("/", os.path.sep)
        except Exception as e:
            print(f"Error al descargar y extraer zip: {e}")
            return None
        
    def is_colab(self):
        try:
            import google.colab
            return True
        except ImportError:
            return False
