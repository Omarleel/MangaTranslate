import os
import time
import cv2
import easyocr
from manga_ocr import MangaOcr
from paddleocr import PaddleOCR

from Utils.Constantes import RUTA_LOCAL_TEMPORAL

class OCRManager:
    def __init__(self, ocr_config):
        self.ocr_config = ocr_config
        self.initialize_ocr_models()

    def initialize_ocr_models(self):
        idioma_easyocr = "ch_sim" if self.ocr_config["easyocr_languages"] == "zh-CN" else self.ocr_config["easyocr_languages"]
        self.lector = easyocr.Reader([idioma_easyocr], gpu=self.ocr_config["use_gpu"])
        self.mocr = MangaOcr()
        self.paddle_motor = {}
        for language in self.ocr_config["paddleocr_languages"]:
            self.paddle_motor[f"paddle_ocr_{language}"] = PaddleOCR(use_angle_cls=True, lang=language, show_log=False)
    
    def perform_easy_ocr_limpieza(self, imagen,  paragraph):
        if paragraph == True:
            resultados_limpieza = self.lector.readtext(
                imagen, paragraph=paragraph,
                batch_size=3,
                beamWidth=3,
                width_ths=0.1,
                height_ths=0.1,
                x_ths=0.05,
                y_ths=0.25,
                min_size=5,
                link_threshold=0.95
            )
        else:
            resultados_limpieza = self.lector.readtext(imagen, paragraph=paragraph)
        return resultados_limpieza
        
    def perform_easy_ocr_traduccion(self, imagen, densidad_globos, idioma_entrada):
        easyocr_config = {
            "Muy denso": {
                "Japonés": {
                    "decoder": "beamsearch",
                    "batch_size": 3,
                    "beamWidth": 3,
                    "width_ths": 0.0,
                    "height_ths": 0.05,
                    "x_ths": 0.05,
                    "y_ths": 0.25,
                    "min_size": 5,
                    "link_threshold": 0.98,
                },
                "Koreano": {
                    "decoder": "beamsearch",
                    "batch_size": 3,
                    "beamWidth": 3,
                    "width_ths": 0.1,
                    "height_ths": 0.05,
                    "x_ths": 0.1,
                    "y_ths": 0.3,
                    "min_size": 5,
                    "link_threshold": 0.95,
                },
                "Chino": {
                    "decoder": "beamsearch",
                    "batch_size": 3,
                    "beamWidth": 3,
                    "width_ths": 0.1,
                    "height_ths": 0.05,
                    "x_ths": 0.1,
                    "y_ths": 0.3,
                    "min_size": 5,
                    "link_threshold": 0.95,
                },
                "Inglés": {
                    "decoder": "beamsearch",
                    "batch_size": 3,
                    "beamWidth": 3,
                    "width_ths": 0.2,
                    "height_ths": 0.78,
                    "x_ths": 0.4,
                    "y_ths": 0.52,
                    "min_size": 5,
                    "link_threshold": 0.98,
                },
            },
            "Poco denso": {
                # Configuración para globos de texto poco densos
                "default": {
                    "decoder": "beamsearch",
                    "batch_size": 3,
                    "beamWidth": 3,
                    "width_ths": 0.22,
                    "height_ths": 0.20,
                    "x_ths": 0.60,
                    "y_ths": 0.50,
                    "min_size": 8,
                    "link_threshold": 0.85,
                },
            },
        }
        configuracion_seleccionada = easyocr_config.get(densidad_globos, {}).get(idioma_entrada, easyocr_config["Poco denso"]["default"])
        resultados_traduccion = self.lector.readtext(
            imagen,
            paragraph=True,
            **configuracion_seleccionada  # Usar ** para desempaquetar el diccionario de configuración
        )
        return resultados_traduccion

    def perform_manga_ocr(self, region_alrededor_pil):
        text = self.mocr(region_alrededor_pil)
        return text

    def perform_paddle_ocr(self, idioma_paddle, region):
        timestamp = int(time.time())
        os.makedirs(RUTA_LOCAL_TEMPORAL, exist_ok=True)
        ruta_archivo_temporal = os.path.join(RUTA_LOCAL_TEMPORAL, f"temp_region_{timestamp}.jpg")
        cv2.imwrite(ruta_archivo_temporal, region)
        resultado_paddle = self.paddle_motor[f"paddle_ocr_{idioma_paddle}"].ocr(ruta_archivo_temporal, cls=False)
        os.remove(ruta_archivo_temporal)

        if not resultado_paddle[0]:
            return ""

        texto = ""
        for i, line in enumerate(resultado_paddle[0]):
            linea_actual = line[-1][0]
            if (i+1) < len(resultado_paddle[0]):  # Si no es la última línea
                texto += linea_actual.replace("~", "")
            else:
                texto += linea_actual

        return texto