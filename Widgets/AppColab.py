from datetime import datetime
import sys
import os
import re
from urllib.parse import unquote
from zipfile import ZipFile
import requests
import ipywidgets as widgets
from IPython.display import display
# Agregar la ruta del directorio raíz (tu_paquete) al sys.path
sys.path.append(os.path.dirname(os.getcwd()))
from Applications.ProcessorColab import Processor
from Applications.Utilities import Utilities
from Utils.Constantes import RUTA_REMOTA, RUTA_LOCAL_ZIPS

class AppColab:   
    def __init__(self, drive_manager):
        self.ruta_pdf_resultante = None
        self.drive_manager = drive_manager
        self.utilities = Utilities()
        self.utilities.download_font_colab(self.drive_manager)
        self.utilities.download_lama_model_colab(self.drive_manager)
        self.nombre_real_archivo = None
        
    def crear_widgets(self):
        self.dropdown_limpieza = widgets.Dropdown(
            options=[
                "Auto",
                "Limpieza básica (B/N)",
                "Limpieza con transparencia",
                "Limpieza a color (Lama)",
                "Limpieza a color (NS)",
                "Limpieza a color (Telea)"
            ],
            value="Auto",
            description="Técnica de limpieza:"
        )
        display(self.dropdown_limpieza)

        self.opcion_analisis = widgets.RadioButtons(
            options=["Por palabra", "Por párrafo"],
            value="Por palabra",
            description="Tipo de detección de texto:"
        )
        display(self.opcion_analisis)

        self.opcion_acciones = widgets.RadioButtons(
            options=["Solo limpiar", "Solo traducir" ,"Limpiar y traducir"],
            value="Limpiar y traducir",
            description="Acciones:"
        )
        display(self.opcion_acciones)

        self.dropdown_idioma_entrada = widgets.Dropdown(
            options=[
                "Japonés",
                "Koreano",
                "Chino",
                "Inglés",
            ],
            value="Japonés",
            description="Traducir del:"
        )
        display(self.dropdown_idioma_entrada)

        self.dropdown_idioma_salida = widgets.Dropdown(
            options=[
                "Español",
                "Inglés",
                "Portugués",
                "Francés",
                "Italiano"
            ],
            value="Español",
            description="Traducir al:"
        )
        display(self.dropdown_idioma_salida)

        self.opcion_densidad_globos = widgets.RadioButtons(
            options=["Muy denso", "Poco denso"],
            value="Muy denso",
            description="Densidad de globos de texto:"
        )
        display(self.opcion_densidad_globos)
        
        self.textbox_batch_size = widgets.Text(
            value='1',  # Valor inicial del textbox
            description='Tamaño del lote:',
            layout=widgets.Layout(width='80%')
        )
        display(self.textbox_batch_size)

        self.textbox_ruta_carpeta = widgets.Text(
            value='',  # Valor inicial del textbox
            description='Ruta de la carpeta:',
            placeholder='Ingrese la ruta de la carpeta o el link...',
            layout=widgets.Layout(width='80%')
        )
        display(self.textbox_ruta_carpeta)

        self.boton_seleccionar_carpeta = widgets.Button(description="Comenzar procesamiento", layout=widgets.Layout(width='250px'))
        self.boton_seleccionar_carpeta.on_click(self.seleccionar_carpeta)
        display(self.boton_seleccionar_carpeta)

        self.etiqueta_info_carga = widgets.Label(value="Cargando: -")
        display(self.etiqueta_info_carga)

        self.progressbar_carga = widgets.FloatProgress(
            value=0,
            min=0,
            max=100,
            description="Carga:",
            bar_style="info"
        )
        display(self.progressbar_carga)

        self.etiqueta_cantidad_imagenes = widgets.Label(value="Cantidad de imágenes: -")
        display(self.etiqueta_cantidad_imagenes)

        self.progressbar_procesamiento = widgets.FloatProgress(
            value=0,
            min=0,
            max=100,
            description="Procesamiento:",
            bar_style="info"
        )
        display(self.progressbar_procesamiento)

        self.boton_descargar_pdf = widgets.Button(description="Descargar archivo pdf", layout=widgets.Layout(width='250px'))
        self.boton_descargar_pdf.on_click(lambda x: self.utilities.descargar_pdf(self.ruta_pdf_resultante))
        display(self.boton_descargar_pdf)
        self.boton_descargar_pdf.disabled = True
        self.processor = Processor(self)
    
    def activar_btn_pdf(self):
        self.boton_descargar_pdf.disabled = False
    def desactivar_btn_pdf(self):
        self.boton_descargar_pdf.disabled = True
        
    def set_ruta_pdf_resultante(self, ruta_pdf_resultante):
        self.ruta_pdf_resultante = ruta_pdf_resultante
        
    def desactivar_botones_y_progressbar(self):
        self.desactivar_btn_pdf()
        self.progressbar_carga.value = 0.0
        self.etiqueta_info_carga.value = "Cargando: -"
        self.etiqueta_cantidad_imagenes.value = "Cantidad de imágenes: -"

    def resetear_valores_iniciales(self):
        self.progressbar_procesamiento.value = 0.0

    def manejar_descarga_drive(self, ruta_carpeta_entrada):
        formato_link_zip = "https://"
        result_download_folder = self.drive_manager.download_folder_by_link(ruta_carpeta_entrada)
        if result_download_folder:
            self.nombre_real_archivo, ruta_carpeta_entrada, ruta_carpeta_salida = result_download_folder
            self.progressbar_carga.value = 100.0
            self.etiqueta_info_carga.value = "Descarga de archivos completada."
            return ruta_carpeta_entrada, ruta_carpeta_salida
        elif ruta_carpeta_entrada.startswith(formato_link_zip):
            return self.manejar_descarga_zip(ruta_carpeta_entrada)
        
        self.etiqueta_info_carga.value = "Error, la ruta o link no es válido."
        exit(0)

    def manejar_descarga_zip(self, ruta_carpeta_entrada):
        os.makedirs(RUTA_LOCAL_ZIPS, exist_ok=True)
        now = datetime.now()
        formatted_date = now.strftime("%d%m%Y%H%M")
        generated_number = int(formatted_date)
        nombre_archivo_zip_temporal = f"tempZip-{generated_number}.zip"
        ruta_archivo_descargado = os.path.join(RUTA_LOCAL_ZIPS, f"{nombre_archivo_zip_temporal}")
        
        response = requests.get(ruta_carpeta_entrada)
        content_type = response.headers.get("content-type")

        if re.search(r'\bzip\b', content_type):
            self.descargar_y_extraer_zip(response, ruta_archivo_descargado)
        else:
            self.etiqueta_info_carga.value = "Error, no es un archivo zip."
            sys.exit(0)
        
        ruta_carpeta_salida = os.path.join(RUTA_REMOTA, f"{self.nombre_real_archivo}")
        self.drive_manager.create_folder(ruta_carpeta_salida)

        return ruta_carpeta_entrada, ruta_carpeta_salida

    def descargar_y_extraer_zip(self, response, ruta_archivo_descargado):
        with open(ruta_archivo_descargado, "wb") as zip_file:
            zip_file.write(response.content)
        content_disposition = response.headers.get("content-disposition")

        if content_disposition:
            self.nombre_real_archivo = unquote(content_disposition.split("filename=")[1]).split('"')[1]
            self.nombre_real_archivo = self.nombre_real_archivo.replace(".zip", "")
        else:
            self.nombre_real_archivo = ruta_archivo_descargado.replace(".zip", "")

        ruta_carpeta_entrada = os.path.join(RUTA_LOCAL_ZIPS, f"{self.nombre_real_archivo}")
        os.makedirs(ruta_carpeta_entrada, exist_ok=True)
        
        self.etiqueta_info_carga.value = "Extrayendo contenido del zip..."
        with ZipFile(ruta_archivo_descargado, "r") as zip_ref:
            zip_ref.extractall(ruta_carpeta_entrada)
        ruta_carpeta_salida = os.path.join(RUTA_REMOTA, f"{self.nombre_real_archivo}") 
        self.copiar_imagenes_drive(ruta_carpeta_entrada, ruta_carpeta_salida)
        os.remove(ruta_archivo_descargado)
        return ruta_carpeta_entrada

    def copiar_imagenes_drive(self, ruta_carpeta_entrada, ruta_carpeta_salida):
        extensiones_permitidas = ['.jpg', '.png', '.jpeg', '.bmp']
        self.drive_manager.create_folder(ruta_carpeta_salida)
        self.etiqueta_info_carga.value = "Copiando imágenes a Google Drive..."
        
        for nombre_archivo in os.listdir(ruta_carpeta_entrada):
            if any(nombre_archivo.endswith(ext) for ext in extensiones_permitidas):
                ruta_origen = os.path.join(ruta_carpeta_entrada, nombre_archivo)
                #ruta_destino = os.path.join(ruta_carpeta_salida, nombre_archivo)
                self.drive_manager.upload_file(ruta_origen, ruta_carpeta_salida, nombre_archivo)
        
        self.etiqueta_info_carga.value = "Descarga y extracción completada."

    def seleccionar_carpeta(self, _):
        self.desactivar_botones_y_progressbar()
        ruta_carpeta_entrada = self.textbox_ruta_carpeta.value
        batch_size = int(self.textbox_batch_size.value)
        self.resetear_valores_iniciales()
        self.drive_manager.create_folder(RUTA_REMOTA)
        ruta_carpeta_entrada, ruta_carpeta_salida = self.manejar_descarga_drive(ruta_carpeta_entrada)
        self.processor.procesar_imagenes(ruta_carpeta_entrada, ruta_carpeta_salida, self.nombre_real_archivo, batch_size)