import re
import sys
import os
import numpy as np
import torch
sys.path.append(os.path.dirname(os.getcwd()))
from Utils.Constantes import COLOR_BLANCO, COLOR_NEGRO, FACTOR_ESPACIO, TAMANIO_MINIMO_FUENTE, RUTA_FUENTE
from Applications.inpainting.lama.inpainting_lama_mpe import LamaMPEInpainter
from Applications.Utilities import Utilities
from shapely.geometry import Polygon
from PIL import Image, ImageDraw, ImageFont
import cv2
import asyncio

class TextImageProcessor:
    def __init__(self):
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.inpainter = LamaMPEInpainter()
        self.utilities = Utilities()
        self.cajas_utilizadas = []
        self.imagen_camuflada = None
        self.imagen_con_alpha = None
        self.ancho_imagen = None
        self.alto_imagen = None
        self.pil_image_limpieza = None
        self.pil_image_traduccion = None
        self.draw_limpieza = None
        self.draw_traduccion = None
        
    def setImagenCamuflada(self, imagen_camuflada):
        self.imagen_camuflada = imagen_camuflada
    def setImagenConAlpha(self, imagen_con_alpha):
        self.imagen_con_alpha = imagen_con_alpha
    
    def setDrawLimpieza(self, draw_limpieza):
        self.draw_limpieza = draw_limpieza
    def setDrawTraduccion(self, draw_traduccion):
        self.draw_traduccion = draw_traduccion
        
    def setAnchoImagen(self, ancho_imagen):
        self.ancho_imagen = ancho_imagen    
    def setAltoImagen(self, alto_imagen):
        self.alto_imagen = alto_imagen

    def encontrar_imagen_mas_grande(self, ruta_carpeta_entrada, lista_archivos):
        imagen_mas_grande = None
        max_ancho = 0
        max_alto = 0

        for archivo in lista_archivos:
            # Carga la imagen y obtén sus dimensiones
            ruta_archivo = os.path.join(ruta_carpeta_entrada, archivo)
            img = Image.open(ruta_archivo)
            ancho, alto = img.size

            # Comprueba si esta imagen es más grande que la imagen más grande actual
            if ancho * alto > max_ancho * max_alto:
                imagen_mas_grande = ruta_archivo
                max_ancho = ancho
                max_alto = alto

        return imagen_mas_grande, max_ancho, max_alto

    def calcular_ancho_texto(self, texto, fuente):
        try:
            return fuente.getbbox(texto)[2] - fuente.getbbox(texto)[0]
        except Exception as e:
            print(f"Error al calcular ancho del texto: {e}")
            return 0

    def calcular_alto_texto(self, texto, fuente):
        try:
            return fuente.getbbox(texto)[3] - fuente.getbbox(texto)[1]
        except Exception as e:
            print(f"Error al calcular alto del texto: {e}")
            return 0

    def reducir_imagen(self, imagen):
        try:
            porcentaje_reduccion = 0.75
            nuevo_alto, nuevo_ancho = [int(dim * porcentaje_reduccion) for dim in imagen.shape[:2]]
            return cv2.resize(imagen, (nuevo_ancho, nuevo_alto))
        except Exception as e:
            print(f"Error al reducir la imagen: {e}")
            return imagen
        
    def dividir_en_parrafos(self, palabras, fuente, widthMax_tra):
        parrafo = []
        linea_actual = ""
        for palabra in palabras:
            texto_linea_actual = " ".join((linea_actual, palabra)).strip()
            if self.calcular_ancho_texto(texto_linea_actual, fuente) > widthMax_tra:
                if len(linea_actual) > 0:
                    parrafo.append(linea_actual)
                linea_actual = palabra
            else:
                linea_actual = texto_linea_actual

        if len(linea_actual) > 0:
            parrafo.append(linea_actual)
        
        return parrafo

    def obtener_propiedades_fuente(self, ancho_caja, alto_caja, texto):
        numero_de_caracteres = max(len(texto), 1)
        max_size = 100

        # Valores predeterminados
        tamanio_fuente = TAMANIO_MINIMO_FUENTE
        fuente = ImageFont.truetype(RUTA_FUENTE, tamanio_fuente)
        alto_parrafo = 0
        espacio_entre_lineas = min(TAMANIO_MINIMO_FUENTE + 2, tamanio_fuente * FACTOR_ESPACIO)

        draw = ImageDraw.Draw(Image.new('RGB', (1, 1)))  # Un único objeto ImageDraw

        for tamanio_fuente in range(TAMANIO_MINIMO_FUENTE, max_size + 1):
            try:
                fuente = ImageFont.truetype(RUTA_FUENTE, tamanio_fuente)
            except Exception as e:
                print(f"Error al cargar la fuente con tamaño {tamanio_fuente}: {e}")
                break

            espacio_entre_lineas = min(TAMANIO_MINIMO_FUENTE + 2, tamanio_fuente * FACTOR_ESPACIO)
            palabras = texto.split(' ')
            alto_parrafo, ancho_linea_actual, ancho_maximo_linea = 0, 0, 0

            for palabra in palabras:
                text_bbox = draw.textbbox((0, 0), palabra, font=fuente)
                text_width, text_height = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]
                ancho_linea_actual += text_width

                if ancho_linea_actual > ancho_caja:
                    alto_parrafo += text_height + espacio_entre_lineas
                    ancho_linea_actual = text_width
                    ancho_maximo_linea = max(ancho_maximo_linea, ancho_linea_actual)
                else:
                    ancho_maximo_linea = max(ancho_maximo_linea, ancho_linea_actual)

            alto_parrafo += text_height

            if alto_parrafo > alto_caja or ancho_maximo_linea > ancho_caja:
                break

        return fuente, alto_parrafo, espacio_entre_lineas
    
    def reemplazar_caracter_especial(self, texto):
        texto = texto.replace("。", ".")
        texto = texto.replace("？", "?")
        texto = texto.replace("．", ".")
        texto = texto.replace("・", ".")
        texto = texto.replace("！", "!")
        texto = texto.replace("０", "")
        return texto

    def filtrar_bounding_boxes(self, resultados):
        """
        Filtra los bounding boxes que están contenidos en otro en más del 90%.

        :param resultados_limpieza: Lista de bounding boxes.
        :return: Lista filtrada de bounding boxes.
        """
        i = 0
        while i < len(resultados):
            caja_1 = resultados[i][0]
            # Corregir la forma como se obtiene y ensancha el bounding box, hay errores em la sigte logica!!
            puntos = np.array(caja_1, dtype=np.int32).reshape((-1, 1, 2))
            coordenadas_poligono = [(x[0][0], x[0][1]) for x in puntos]
            poligono_1 = Polygon(coordenadas_poligono)

            j = 0
            while j < len(resultados):
                if i == j:
                    j += 1
                    continue
                caja_2 = resultados[j][0]
                puntos2 = np.array(caja_2, dtype=np.int32).reshape((-1, 1, 2))
                coordenadas_poligono2 = [(x[0][0], x[0][1]) for x in puntos2]
                poligono_2 = Polygon(coordenadas_poligono2)

                area_interseccion = poligono_1.intersection(poligono_2).area
                area_poligono_1 = poligono_1.area
                porcentaje_interseccion = (area_interseccion / area_poligono_1) * 100

                if porcentaje_interseccion > 90:
                    del resultados[i]
                    i -= 1
                    break
                j += 1
            i += 1

        return resultados

    def fusionar_cajas(self, cajas, umbral_x=5, umbral_y=5):
        if not cajas:
            return []

        def punto_medio(caja):
            x_mid = (caja[0][0] + caja[2][0]) / 2
            y_mid = (caja[0][1] + caja[2][1]) / 2
            return x_mid, y_mid

        cajas_fusionadas = []

        while cajas:
            caja_actual = cajas.pop(0)

            for i, otra_caja in enumerate(cajas):
                # Calcula puntos medios de las cajas
                x_mid_actual, y_mid_actual = punto_medio(caja_actual)
                x_mid_otra, y_mid_otra = punto_medio(otra_caja)

                # Comprueba si las cajas están suficientemente cerca en el eje Y
                cercania_vertical = abs(y_mid_actual - y_mid_otra) <= umbral_y

                # Comprueba si las cajas están suficientemente cerca en el eje X
                cercania_horizontal = abs(x_mid_actual - x_mid_otra) <= umbral_x

                # Si las cajas están cerca en el eje horizontal y vertical
                if cercania_horizontal and cercania_vertical:
                    x_min = min(caja_actual[0][0], otra_caja[0][0])
                    y_min = min(caja_actual[0][1], otra_caja[0][1])
                    x_max = max(caja_actual[2][0], otra_caja[2][0])
                    y_max = max(caja_actual[2][1], otra_caja[2][1])
                    caja_actual = [(x_min, y_min), (x_max, y_min), (x_max, y_max), (x_min, y_max)]
                    del cajas[i]
                    break

            cajas_fusionadas.append(caja_actual)

        return cajas_fusionadas
    
    def validar_texto(self, texto, fuente, widthMax_tra, heightMax_tra):
        total_caracteres = len(texto)
        caracteres_alfabeticos = sum(1 for char in texto if char.isalpha())

        if total_caracteres <= 1 or caracteres_alfabeticos <= 1:
            return False

        area_caja = heightMax_tra * widthMax_tra
        _, _, ancho_texto, alto_texto = fuente.getbbox(texto)
        
        if total_caracteres > 5 and total_caracteres < 15:
            
            area_texto = ancho_texto * alto_texto
            ratio = area_texto / area_caja

            if ratio < 0.095:
                return False
        if caracteres_alfabeticos <= 5 and alto_texto > self.alto_imagen * 0.028:
            return False

        # Contar símbolos (considerando ... como uno solo)
        total_puntos_suspensivos = texto.count("...")
        total_simbolos = sum(1 for caracter in texto if not caracter.isalnum() and caracter not in [' ', '\t', '\n', '\r'])
        # Ajuste para puntos suspensivos.
        total_simbolos -= 2 * total_puntos_suspensivos
        proporcion_simbolos = total_simbolos / total_caracteres

        # Contar números.
        total_numeros = sum(1 for caracter in texto if caracter.isdigit())
        proporcion_numeros = total_numeros / total_caracteres
        
        # Validaciones sobre las proporciones de símbolos y números.
        if proporcion_simbolos >= 0.6 or proporcion_numeros >= 0.99:
            return False
        return True
    
    def reducir_vocales(self, texto):
        # La expresión regular busca cualquier vocal (mayúscula o minúscula) que se repite 
        # 4 o más veces y la reemplaza por solo 3 ocurrencias de esa vocal.
        return re.sub(r'([aeiouAEIOU])\1{3,}', r'\1\1\1', texto)
    
    def ajustar_tam_fuente_ancho(self, parrafo, fuente, espacio_entre_lineas, widthMax_tra):
        for i, linea in enumerate(parrafo):
            anchoLinea = self.calcular_ancho_texto(linea, fuente)
            while anchoLinea > widthMax_tra:
                tamanio_fuente = fuente.size - 1
                tamanio_fuente = max(TAMANIO_MINIMO_FUENTE, tamanio_fuente)
                fuente = ImageFont.truetype(RUTA_FUENTE, tamanio_fuente)
                espacio_entre_lineas = min(TAMANIO_MINIMO_FUENTE + 2, tamanio_fuente * FACTOR_ESPACIO)
                if tamanio_fuente == TAMANIO_MINIMO_FUENTE:
                    break
                anchoLinea = self.calcular_ancho_texto(linea, fuente)

        return fuente, espacio_entre_lineas

    def ajustar_tam_fuente_altura(self, parrafo, fuente, espacio_entre_lineas, heightMax_tra):
        excede_altura = True
        while excede_altura:
            altoParrafo = sum([self.calcular_alto_texto(linea, fuente) for linea in parrafo])
            altoParrafo += (len(parrafo) - 1) * espacio_entre_lineas

            if altoParrafo > heightMax_tra:
                tamanio_fuente = fuente.size - 1
                tamanio_fuente = max(TAMANIO_MINIMO_FUENTE, tamanio_fuente)
                if tamanio_fuente == TAMANIO_MINIMO_FUENTE:
                    excede_altura = False
                fuente = ImageFont.truetype(RUTA_FUENTE, tamanio_fuente)
                espacio_entre_lineas = min(TAMANIO_MINIMO_FUENTE + 2, tamanio_fuente * FACTOR_ESPACIO)
            else:
                excede_altura = False

        return fuente, espacio_entre_lineas

    def dibujar_texto(self, parrafo, altoParrafo, fuente, espacio_entre_lineas, x_min, y_min, w_tra, heightMax_tra, colorBorde, colorTexto):
        # Calcula márgenes y espacios
        margen_superior = (heightMax_tra - altoParrafo) / 2 if heightMax_tra > altoParrafo else 0
        desplazamiento_bordes = 5

        try:
            y_texto = y_min + margen_superior

            # Dibuja texto y bordes
            for i, linea in enumerate(parrafo):
                # Asegúrate de que el alto de línea se calcula aquí, dentro del bucle, para cada línea
                alto_linea = self.calcular_alto_texto(linea, fuente)
                text_bbox = self.draw_traduccion.textbbox((x_min, y_texto), linea, font=fuente)
                anchoLinea = text_bbox[2] - text_bbox[0]
                x_texto = x_min + (w_tra - anchoLinea) // 2
                
                # Dibujar bordes varias veces para crear el efecto de grosor
                for j in range(desplazamiento_bordes):
                    for dx, dy in [(-0.5, -0.5), (-0.5, 0.5), (0.5, 0.5), (0.5, -0.5)]:
                        pos_bordes = (x_texto + j * dx, y_texto + j * dy)
                        self.draw_traduccion.text(pos_bordes, linea, font=fuente, fill=colorBorde)
                
                # Dibujar texto encima de los bordes
                self.draw_traduccion.text((x_texto, y_texto), linea, font=fuente, fill=colorTexto)

                # Incrementa y_texto por el alto de la línea y el espacio entre líneas
                y_texto += alto_linea + espacio_entre_lineas

            return True
        except Exception as e:
            print(f"Error al dibujar texto: {e}")
            return False

        
    def obtener_mascara_texto(self, formato_manga, tipo_limpieza, caja_lim, promedio_color_lim, area_gris_lim):
        try:
            # Procesamiento de limpieza según tipo
            if tipo_limpieza == "Limpieza básica (B/N)" or (tipo_limpieza == "Auto" and formato_manga == "Blanco y negro (B/N)"):
                if np.mean(promedio_color_lim) >= 128:  # Predomina el color blanco
                    _, mascara_texto = cv2.threshold(area_gris_lim, 200, 255, cv2.THRESH_BINARY)
                else:
                    _, mascara_texto = cv2.threshold(area_gris_lim, 150, 255, cv2.THRESH_BINARY_INV)

                expansion = round(self.ancho_imagen / 80)
                kernel = np.ones((expansion, expansion), np.uint8)
                mascara_texto = cv2.morphologyEx(mascara_texto, cv2.MORPH_ERODE, kernel)

            elif tipo_limpieza == "Limpieza con transparencia":
                if formato_manga == "Color":
                    _, mascara_texto = cv2.threshold(area_gris_lim, 200, 255, cv2.THRESH_BINARY)
                else:
                    if np.mean(promedio_color_lim) >= 128:  # Predomina el color blanco
                        _, mascara_texto = cv2.threshold(area_gris_lim, 200, 255, cv2.THRESH_BINARY)
                    else:
                        _, mascara_texto = cv2.threshold(area_gris_lim, 150, 255, cv2.THRESH_BINARY_INV)

                expansion = round(self.ancho_imagen / 80)
                kernel = np.ones((expansion, expansion), np.uint8)
                mascara_texto = cv2.morphologyEx(mascara_texto, cv2.MORPH_ERODE, kernel)

            elif (tipo_limpieza == "Limpieza a color (NS)" or 
                tipo_limpieza == "Limpieza a color (Telea)" or tipo_limpieza == "Limpieza a color (Lama)") or (tipo_limpieza == "Auto" and formato_manga == "Color"):
                if np.mean(promedio_color_lim) >= 128:  # Predomina el color blanco
                    _, mascara_texto = cv2.threshold(area_gris_lim, 200, 255, cv2.THRESH_BINARY)
                else:
                    _, mascara_texto = cv2.threshold(area_gris_lim, 150, 255, cv2.THRESH_BINARY_INV)

                expansion = round(self.ancho_imagen / 80)
                kernel = np.ones((expansion, expansion), np.uint8)
                mascara_texto = cv2.morphologyEx(mascara_texto, cv2.MORPH_ERODE, kernel)
                    
            mascara_texto_invertida = cv2.bitwise_not(mascara_texto)
            return mascara_texto_invertida

        except Exception as e:
            print(f"Error al obtener mascara: {e}")
            return False
    
    def aplicar_relleno_solido(self, formato_manga, tipo_limpieza, coordenadas_caja_lim, promedio_color_lim, area_gris_lim):
        if tipo_limpieza == "Limpieza básica (B/N)" or (tipo_limpieza == "Auto" and formato_manga == "Blanco y negro (B/N)"):
            if np.mean(promedio_color_lim) >= 128: #Predomina el color blanco
                color_lim = COLOR_BLANCO
                _, mascara_texto = cv2.threshold(area_gris_lim, 200, 255, cv2.THRESH_BINARY)
            else:
                color_lim = COLOR_NEGRO
                _, mascara_texto = cv2.threshold(area_gris_lim, 150, 255, cv2.THRESH_BINARY_INV)

            expansion = round(self.ancho_imagen * 10 / 1280)
            kernel = np.ones((expansion, expansion), np.uint8)
            mascara_texto = cv2.morphologyEx(mascara_texto, cv2.MORPH_ERODE, kernel)

            # Dibuja sobre la máscara de texto existente
            coordenadas_negras = np.column_stack(np.where(mascara_texto == 0))
            for coordenada in coordenadas_negras:
                # Ajusta las coordenadas al área delimitada por x_lim, y_lim
                x, y = coordenada[1] + coordenadas_caja_lim["x_lim"], coordenada[0] + coordenadas_caja_lim["y_lim"]
                self.draw_limpieza.point((x, y), fill=color_lim)
                self.draw_traduccion.point((x, y), fill=color_lim)
                
    def aplicar_inpainting(self, formato_manga, tipo_limpieza, mascara):
        if tipo_limpieza == "Limpieza a color (Lama)" or (tipo_limpieza == "Auto" and formato_manga == "Color"):
            if self.utilities.is_colab() == True:
                import nest_asyncio
                nest_asyncio.apply()
                loop = asyncio.get_event_loop()
            else:
                asyncio.set_event_loop(asyncio.new_event_loop())
                loop = asyncio.get_event_loop()
            self.imagen_camuflada = loop.run_until_complete(self.inpaint_with_lama(self.imagen_camuflada, mascara))
        elif tipo_limpieza == "Limpieza a color (NS)":
            self.imagen_camuflada = cv2.inpaint(self.imagen_camuflada, mascara, 3, cv2.INPAINT_NS)
        else:
            # Limpieza a color (Telea)
            self.imagen_camuflada = cv2.inpaint(self.imagen_camuflada, mascara, 3, cv2.INPAINT_TELEA)
        
        if tipo_limpieza in ["Limpieza a color (Lama)", "Auto", "Limpieza a color (NS)", "Limpieza a color (Telea)"]:
            pil_image_camuflada_limpieza = Image.fromarray(cv2.cvtColor(self.imagen_camuflada, cv2.COLOR_BGR2RGB))
            self.pil_image_limpieza.paste(pil_image_camuflada_limpieza, (0, 0))
            self.pil_image_traduccion.paste(pil_image_camuflada_limpieza, (0, 0))
        
    async def inpaint_with_lama(self, image, mask):
        await self.inpainter._load(device=self.device)
        inpainted_image = await self.inpainter._infer(image, mask)
        return inpainted_image