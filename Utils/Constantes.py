import os
# CONSTANTES
def construir_ruta(base, *paths):
    return os.path.join(base, *paths).replace("/", os.path.sep)

RUTA_ACTUAL = os.getcwd()
RUTA_REMOTA = "/Traductor de Mangas"

RUTA_LOCAL_MODELO_INPAINTING = construir_ruta(RUTA_ACTUAL, "Models", "inpainting")
RUTA_MODELO_LAMA = construir_ruta(RUTA_LOCAL_MODELO_INPAINTING, "inpainting_lama_mpe.ckpt")
RUTA_LOCAL_FUENTES = construir_ruta(RUTA_ACTUAL, "fonts")
RUTA_FUENTE = construir_ruta(RUTA_ACTUAL, "fonts", "NewWildWordsRoman.ttf")
RUTA_LOCAL_PDFS = construir_ruta(RUTA_ACTUAL, "pdfs")
RUTA_LOCAL_ZIPS = construir_ruta(RUTA_ACTUAL, "zips")
RUTA_LOCAL_SALIDA = construir_ruta(RUTA_ACTUAL, "Outputs")
RUTA_LOCAL_TEMPORAL = construir_ruta(RUTA_ACTUAL, "temp")

TAMANIO_MINIMO_FUENTE = 12
FACTOR_ESPACIO = 0.42
URL_FUENTE = "https://drive.google.com/file/d/1uIAh-nGGi04f-7moWsKvRhTbAj-Oq84O/view?usp=sharing"
URL_MODELO_LAMA = "https://drive.google.com/file/d/1Qvop0I9_p6EnbZTJO9A_LLUEgwUkZ4T8/view?usp=sharing"

COLOR_BLANCO = (255, 255, 255)
COLOR_NEGRO = (0, 0, 0)