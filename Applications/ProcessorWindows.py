import sys
import os
sys.path.append(os.path.dirname(os.getcwd()))
from Utils.Constantes import RUTA_LOCAL_PDFS, RUTA_LOCAL_TEMPORAL, COLOR_BLANCO, COLOR_NEGRO
from Applications.TextImageProcessor import TextImageProcessor
from Applications.Utilities import Utilities
from Applications.OCRManager import OCRManager
from Applications.BubbleDetector import BubbleDetector
from Applications.JsonGenerator import JsonGenerator

import time
import numpy as np
import re
from natsort import natsorted
from PIL import ImageDraw, Image
from reportlab.pdfgen import canvas
import cv2
import torch
from shapely.geometry import Polygon

class Processor:
    def __init__(self, app_window):
        self.app_window = app_window
        self.text_image_processor = TextImageProcessor()
        self.utilities = Utilities()
        self.json_transcripcion = JsonGenerator()
        self.json_traduccion = JsonGenerator()
       
        self.indice_imagen = 0
        self.formato_manga = None
        self.densidad_globos = None
        self.valores_traduccion = []
        self.mascara_global = None
        # Instanciar herramientas OCR
        use_gpu = torch.cuda.is_available() # Verifica si CUDA está disponible
        idioma_easyocr, _ = self.utilities.obtener_abreviacion_idioma(self.app_window.dropdown_idioma_entrada.currentText(), "")
        ocr_config = {
            "easyocr_languages": idioma_easyocr,
            "paddleocr_languages": ["en", "korean", "ch"],
            "use_gpu": use_gpu
        }
        self.ocr_manager = OCRManager(ocr_config)  
        
    def emitir_proceso(self, cantidad_imagenes, nombre_imagen, valor_progreso):
        self.app_window.imagen_procesada_signal.emit(cantidad_imagenes, nombre_imagen, valor_progreso)
        
    def procesar_imagenes(self, ruta_carpeta_entrada, ruta_carpeta_salida, nombre_real_archivo, is_running):
        self.json_transcripcion.agregar_entrada('Título', nombre_real_archivo)
        self.json_traduccion.agregar_entrada('Título', nombre_real_archivo)
        # Restablece el valor del progressbar en la ventana principal
        self.app_window.progressbar_procesamiento.setValue(int(self.indice_imagen))

        archivos = os.listdir(ruta_carpeta_entrada)
        archivos_imagen = [
            archivo for archivo in archivos if archivo.lower().endswith(('.jpg', '.png', '.jpeg', '.bmp'))
        ]
        cantidad_imagenes = len(archivos_imagen)
        self.json_transcripcion.agregar_entrada('Páginas', cantidad_imagenes)
        self.json_traduccion.agregar_entrada('Páginas', cantidad_imagenes)
        
        self.total_imagenes = cantidad_imagenes
        self.emitir_proceso(cantidad_imagenes, "-", "-")
        # self.app_window.etiqueta_cantidad_imagenes.setText(f"Cantidad de imágenes: {cantidad_imagenes}")

        idioma_entrada = self.app_window.dropdown_idioma_entrada.currentText()
        tipo_limpieza = self.app_window.dropdown_limpieza.currentText()
        # Ordena los archivos
        archivos_imagen = natsorted(archivos_imagen)
        # Genera un archivo PDF
        ruta_archivos_pdf = RUTA_LOCAL_PDFS
        if not os.path.exists(ruta_archivos_pdf):
            os.makedirs(ruta_archivos_pdf)
        ruta_pdf_resultante = os.path.join(ruta_archivos_pdf, f"{nombre_real_archivo}.pdf")
        
        _, ancho_mas_grande, alto_mas_grande = self.text_image_processor.encontrar_imagen_mas_grande(ruta_carpeta_entrada, archivos_imagen)
        self.json_transcripcion.agregar_entrada('Resolución', [ancho_mas_grande, alto_mas_grande])
        self.json_traduccion.agregar_entrada('Resolución', [ancho_mas_grande, alto_mas_grande])
        
        pagesize_pdf = (ancho_mas_grande, alto_mas_grande)
        canvas_pdf = canvas.Canvas(ruta_pdf_resultante, pagesize=pagesize_pdf)
        opcion_acciones = self.app_window.opcion_accion.currentText()
        os.makedirs(ruta_carpeta_salida, exist_ok=True)
        ruta_resultado_limpieza = os.path.join(ruta_carpeta_salida, "Limpieza")
        ruta_resultado_traduccion = os.path.join(ruta_carpeta_salida, "Traducción")
        # Procesa cada imagen en la carpeta
        for archivo in archivos_imagen:
            if not is_running.is_set():
                break
            # Calcula el valor de progreso
            valor_progreso = (self.indice_imagen / self.total_imagenes) * 100
            # Actualiza la barra de progreso después de un breve retraso
            self.emitir_proceso(cantidad_imagenes, archivo, int(valor_progreso))
            # Procesar imagenes
            imagen, imagen_copia, resultados_limpieza, resultados_traduccion = self.preparar_imagenes(archivo, ruta_carpeta_entrada)
            self.text_image_processor.setImagenCamuflada(imagen.copy())
            # Crear imágenes PIL para limpieza y traducción
            self.text_image_processor.pil_image_limpieza = Image.fromarray(cv2.cvtColor(imagen, cv2.COLOR_BGR2RGB))
            self.text_image_processor.setDrawLimpieza(ImageDraw.Draw(self.text_image_processor.pil_image_limpieza))

            self.text_image_processor.pil_image_traduccion = Image.fromarray(cv2.cvtColor(imagen, cv2.COLOR_BGR2RGB))
            self.text_image_processor.setDrawTraduccion(ImageDraw.Draw(self.text_image_processor.pil_image_traduccion))
            if self.proceso_terminado:
                continue
            # Inciar con la traduccion del manga
            self.limpiar_manga_1(imagen, imagen_copia, resultados_limpieza, resultados_traduccion, idioma_entrada)
            imagen_limpia = np.asarray(self.text_image_processor.pil_image_limpieza)
            imagen_limpia = cv2.cvtColor(imagen_limpia, cv2.COLOR_RGB2BGR)

            self.traducir_manga()
            self.valores_traduccion.clear()
            
            imagen_traducida = np.asarray(self.text_image_processor.pil_image_traduccion)
            imagen_traducida = cv2.cvtColor(imagen_traducida, cv2.COLOR_RGB2BGR)

            if opcion_acciones == "Solo limpiar":
                self.app_window.file_manager.create_folder(ruta_resultado_limpieza)
            elif opcion_acciones == "Solo traducir":
                self.app_window.file_manager.create_folder(ruta_resultado_traduccion)
            elif opcion_acciones == "Limpiar y traducir":
                self.app_window.file_manager.create_folder(ruta_resultado_limpieza)
                self.app_window.file_manager.create_folder(ruta_resultado_traduccion)

            if tipo_limpieza == "Limpieza con transparencia":
                archivo_png = os.path.splitext(archivo)[0] + ".png"
                script_path = os.getcwd()
                os.chdir(ruta_resultado_limpieza)
                cv2.imwrite(archivo_png, self.text_image_processor.imagen_con_alpha) # Guardar la imagen resultante en formato PNG
                os.chdir(script_path)
            else:
                ruta_temporal_lim = os.path.join(RUTA_LOCAL_TEMPORAL, f"lim_{archivo}")
                ruta_temporal_tra = os.path.join(RUTA_LOCAL_TEMPORAL, f"tra_{archivo}")
                os.makedirs(RUTA_LOCAL_TEMPORAL, exist_ok=True)
                if opcion_acciones == "Limpiar y traducir":
                    cv2.imwrite(ruta_temporal_lim, imagen_limpia)
                    self.app_window.file_manager.upload_file(ruta_temporal_lim, ruta_resultado_limpieza, archivo)
                    cv2.imwrite(ruta_temporal_tra, imagen_traducida)
                    self.app_window.file_manager.upload_file(ruta_temporal_tra, ruta_resultado_traduccion, archivo)
                    self.utilities.generar_pdf(self.indice_imagen, canvas_pdf, ruta_temporal_tra)
                    os.remove(ruta_temporal_lim)
                    os.remove(ruta_temporal_tra)
                elif opcion_acciones == "Solo limpiar":
                    cv2.imwrite(ruta_temporal_lim, imagen_limpia)
                    self.app_window.file_manager.upload_file(ruta_temporal_lim, ruta_resultado_limpieza, archivo)
                    os.remove(ruta_temporal_lim)
                elif opcion_acciones == "Solo traducir":
                    cv2.imwrite(ruta_temporal_tra, imagen_traducida)
                    self.app_window.file_manager.upload_file(ruta_temporal_tra, ruta_resultado_traduccion, archivo)
                    self.utilities.generar_pdf(self.indice_imagen, canvas_pdf, ruta_temporal_tra)
                    os.remove(ruta_temporal_tra)
                    
            # Incrementa el valor de imagen_actual
            self.indice_imagen += 1
            # Libera la memoria de la imagen y los resultados
            del imagen, imagen_copia, self.mascara_global, resultados_limpieza, resultados_traduccion

        self.emitir_proceso(cantidad_imagenes, "Completado", 100)
        
        ruta_transcripcion = os.path.join(ruta_carpeta_salida, 'transcripcion.json')
        ruta_traduccion = os.path.join(ruta_carpeta_salida, 'traduccion.json')
        self.json_transcripcion.guardar_en_archivo(ruta_transcripcion)
        self.json_traduccion.guardar_en_archivo(ruta_traduccion)
        if opcion_acciones == "Solo traducir" or opcion_acciones == "Limpiar y traducir" and tipo_limpieza != "Limpieza con transparencia":
            self.utilities.guardar_pdf()
            self.app_window.file_manager.upload_file(ruta_pdf_resultante, ruta_carpeta_salida)
            self.app_window.set_ruta_pdf_resultante(ruta_pdf_resultante)
            self.app_window.activar_btn_pdf()
        self.indice_imagen = 0
            
    def preparar_imagenes(self, archivo, ruta_carpeta_entrada):
        self.proceso_terminado = False

        # Obtiene la ruta completa del archivo
        ruta_archivo = os.path.join(ruta_carpeta_entrada, archivo)

        # Carga la imagen utilizando OpenCV
        with open(ruta_archivo, 'rb') as f:
            byte_array = f.read()

        # Convertir a numpy array
        image_nparr = np.frombuffer(byte_array, np.uint8)

        # Decodificar usando OpenCV
        imagen = cv2.imdecode(image_nparr, cv2.IMREAD_COLOR)
        imagen_copia = imagen.copy()

        # Convierte la imagen con canal alfa
        self.text_image_processor.setImagenConAlpha(cv2.cvtColor(imagen, cv2.COLOR_BGR2BGRA, cv2.IMREAD_UNCHANGED))

        # Convierte la imagen a escala de grises
        imagen_gris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)

        for intento in range(3):
            try:
                # Configuración de reconocimiento de texto común
                paragraph = self.app_window.rb_parrafo.isChecked()
                idioma_entrada = self.app_window.dropdown_idioma_entrada.currentText()
                self.densidad_globos = self.app_window.opcion_densidad_globos.checkedButton().text()
                memoria_suficiente = False

                while not memoria_suficiente:
                    try:
                        # Configuración específica para densidad de globos y idioma de entrada
                        resultados_traduccion = self.ocr_manager.perform_easy_ocr_traduccion(imagen, self.densidad_globos, idioma_entrada)
                        # Marca como True si el reconocimiento de texto fue exitoso sin errores de memoria
                        memoria_suficiente = True

                    except (torch.cuda.CudaError, RuntimeError) as e:
                        print(f"Error (intento {intento+1}): {e}")
                        # Si hay un error de memoria u otro error de tiempo de ejecución, libera la memoria y espera antes de volver a intentar
                        torch.cuda.empty_cache()
                        time.sleep(2)
                        intento += 1
                        imagen = self.text_image_processor.reducir_imagen(imagen)
                        self.text_image_processor.imagen_con_alpha = cv2.cvtColor(imagen, cv2.COLOR_BGR2BGRA, cv2.IMREAD_UNCHANGED)
                        imagen_gris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
                        break

                if memoria_suficiente:
                    # Realiza cualquier otra operación necesaria con los resultados
                    resultados_limpieza = self.ocr_manager.perform_easy_ocr_limpieza(imagen_gris, paragraph=paragraph)
                    return imagen, imagen_copia, resultados_limpieza, resultados_traduccion

            except Exception as e:
                print(f"Error (intento {intento+1}): {e}")
                # Maneja cualquier otro error que pueda ocurrir
                intento += 1
                imagen = self.text_image_processor.reducir_imagen(imagen)
                self.text_image_processor.imagen_con_alpha = cv2.cvtColor(imagen, cv2.COLOR_BGR2BGRA, cv2.IMREAD_UNCHANGED)
                imagen_gris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)

        self.proceso_terminado = True
        
    def limpiar_manga_1(self, imagen, imagen_copia, resultados_limpieza, resultados_traduccion, idioma_entrada):
        self.text_image_processor.setAnchoImagen(imagen_copia.shape[1])
        self.text_image_processor.setAltoImagen(imagen_copia.shape[0])
        
        self.mascara_global = np.zeros(imagen.shape[:2], dtype=np.uint8)
        imagen_gris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
        valor_medio = cv2.mean(imagen_gris)[0]

        # Si el valor medio es cercano a 0 o 255, es probable que la imagen esté en escala de grises
        if valor_medio < 50 or valor_medio > 200:
            self.formato_manga = "Blanco y negro (B/N)"
        else:
            self.formato_manga = "Color"
        
        self.json_transcripcion.agregar_elemento_a_lista('Transcripción', {
            'Página': self.indice_imagen + 1,
            'Formato': self.formato_manga,
            'Globos de texto': []
        })
        self.json_traduccion.agregar_elemento_a_lista('Traducción', {
            'Página': self.indice_imagen + 1,
            'Formato': self.formato_manga,
            'Globos de texto': []
        })
        
        resultados_traduccion = self.text_image_processor.filtrar_bounding_boxes(resultados_traduccion)
        if self.densidad_globos == "Poco denso":
            cajas = [resultado[0] for resultado in resultados_traduccion]
            resultados_traduccion = self.text_image_processor.fusionar_cajas(cajas, 8, 5)
        
        for resultado_traduccion in resultados_traduccion:
            if self.densidad_globos == "Poco denso":
                caja_traduccion = resultado_traduccion
            else:
                caja_traduccion = resultado_traduccion[0]
            puntos_tra = np.array(caja_traduccion, dtype=np.int32).reshape((-1, 1, 2))

            x_tra, y_tra, w_tra, h_tra = cv2.boundingRect(puntos_tra)
            # Ajusta las coordenadas para asegurarte de que estén dentro de los límites de la imagen
            x_tra = max(0, x_tra)
            y_tra = max(0, y_tra)
            w_tra = min(w_tra, imagen.shape[1] - x_tra)
            h_tra = min(h_tra, imagen.shape[0] - y_tra)

            # Calcula las coordenadas para la región con el margen
            x_margin_tra = max(0, x_tra - 5)
            y_margin_tra = max(0, y_tra - 5)
            widthMax_tra = min(w_tra + 5, imagen.shape[1] - x_margin_tra)
            heightMax_tra = min(h_tra + 5, imagen.shape[0] - y_margin_tra)
            
            # Calcula la región con el margen alrededor de las coordenadas ajustadas
            region_alrededor = imagen_copia[y_margin_tra:y_margin_tra + heightMax_tra, x_margin_tra:x_margin_tra + widthMax_tra]
            region_alrededor_pil = Image.fromarray(region_alrededor)
            promedio_color = cv2.mean(region_alrededor)[:3]
            if np.mean(promedio_color) < 128:
                colorBorde = COLOR_NEGRO
                colorTexto = COLOR_BLANCO
            else:
                colorBorde = COLOR_BLANCO
                colorTexto = COLOR_NEGRO
            idioma_entrada = self.app_window.dropdown_idioma_entrada.currentText()
            if idioma_entrada == "Japonés":
                texto = self.ocr_manager.perform_manga_ocr(region_alrededor_pil)

            elif idioma_entrada in ["Koreano", "Chino"]:
                paddle_idioma = "korean" if idioma_entrada == "Koreano" else "ch"
                texto = self.ocr_manager.perform_paddle_ocr(paddle_idioma, region_alrededor)

            elif idioma_entrada == "Inglés":
                paddle_idioma = "en"
                texto = self.ocr_manager.perform_paddle_ocr(paddle_idioma, region_alrededor)
                texto = re.sub(r'(?<=[a-zA-Z])\.(?=[a-zA-Z])', '. ', texto)
                oraciones = texto.split('. ')
                texto = '. '.join(oracion.capitalize() for oracion in oraciones)

            texto_traducido = self.utilities.traducir_texto(texto, self.app_window.dropdown_idioma_entrada.currentText(), self.app_window.dropdown_idioma_salida.currentText())
            if texto_traducido is not None and len(texto_traducido.split()) > 0:
                texto_traducido = self.text_image_processor.reemplazar_caracter_especial(texto_traducido)
                fuente, altoParrafo, espacio_entre_lineas = self.text_image_processor.obtener_propiedades_fuente(widthMax_tra, heightMax_tra, texto_traducido)
                texto_traducido = self.text_image_processor.reducir_vocales(texto_traducido)
                if self.text_image_processor.validar_texto(texto_traducido, fuente, widthMax_tra, heightMax_tra) == False:
                    continue                
                palabras = texto_traducido.split(" ")
                self.limpiar_manga_2(imagen, resultados_limpieza, puntos_tra, colorTexto)
            else:
                continue
            centroide_x = x_tra + w_tra // 2
            centroide_y = y_tra + h_tra // 2
            
            self.json_transcripcion.agregar_a_sublista(
                'Transcripción', self.indice_imagen,
                'Globos de texto', {
                    'Coordenadas': [centroide_x, centroide_y],
                    'Texto': texto
                }
            )
            self.json_traduccion.agregar_a_sublista(
                'Traducción', self.indice_imagen,
                'Globos de texto', {
                    'Coordenadas': [centroide_x, centroide_y],
                    'Texto': texto_traducido
                }
            )
            # Extraer las coordenadas de la caja y asegurarse de que sean enteros
            x_min, y_min = x_tra , y_tra

            parrafo = self.text_image_processor.dividir_en_parrafos(palabras, fuente, widthMax_tra)
            # Reajustar el tamaño de la fuente en función de la anchura
            fuente, espacio_entre_lineas = self.text_image_processor.ajustar_tam_fuente_ancho(parrafo, fuente, espacio_entre_lineas, widthMax_tra)
            # Reajustar el tamaño de la fuente en función de la altura
            fuente, espacio_entre_lineas = self.text_image_processor.ajustar_tam_fuente_altura(parrafo, fuente, espacio_entre_lineas, heightMax_tra)

            valores_tra = {
                'parrafo': parrafo,
                'altoParrafo': altoParrafo,
                'fuente': fuente,
                'espacio_entre_lineas': espacio_entre_lineas,
                'x_min': x_min,
                'y_min': y_min,
                'w_tra': w_tra,
                'heightMax_tra': heightMax_tra,
                'colorBorde': colorBorde,
                'colorTexto': colorTexto
            }
            self.valores_traduccion.append(valores_tra)
                
    def limpiar_manga_2(self, imagen, resultados_limpieza, puntos_tra, colorTexto):
        tipo_limpieza =  self.app_window.dropdown_limpieza.currentText()
        resultados_limpieza = self.text_image_processor.filtrar_bounding_boxes(resultados_limpieza)           
        for resultado_lim in resultados_limpieza:
            caja_lim = resultado_lim[0]
            puntos_lim = np.array(caja_lim, dtype=np.int32).reshape((-1, 1, 2))
            coordenadas_poligono_lim = [(x[0][0], x[0][1]) for x in puntos_lim]
            coordenadas_poligono_tra = [(x[0][0], x[0][1]) for x in puntos_tra]
            x_lim, y_lim, w_lim, h_lim = cv2.boundingRect(puntos_lim)
            poligono_lim = Polygon(coordenadas_poligono_lim)
            poligono_tra = Polygon(coordenadas_poligono_tra)
            x_lim = max(0, x_lim)
            y_lim = max(0, y_lim)
            w_lim = min(w_lim, imagen.shape[1] - x_lim)
            h_lim = min(h_lim, imagen.shape[0] - y_lim)
            coordenadas_caja_lim = {"x_lim": x_lim, "y_lim": y_lim, "w_lim": w_lim, "h_lim": h_lim}

            x_margin_lim = max(0, x_lim - 5)
            y_margin_lim = max(0, y_lim - 5)
            widthMax_lim = min(w_lim + 5, imagen.shape[1] - x_margin_lim)
            heightMax_lim = min(h_lim + 5, imagen.shape[0] - y_margin_lim)

            region_alrededor_lim = imagen[y_margin_lim:y_margin_lim + heightMax_lim, x_margin_lim:x_margin_lim + widthMax_lim]
            area_texto_lim = imagen[y_lim:y_lim + h_lim, x_lim:x_lim + w_lim]
            area_gris_lim = cv2.cvtColor(area_texto_lim, cv2.COLOR_BGR2GRAY)
            
            if colorTexto == COLOR_NEGRO:
                mascara_excluir = cv2.inRange(region_alrededor_lim, np.array([0, 0, 0]), np.array([60, 60, 60]))
            else:
                mascara_excluir = cv2.inRange(region_alrededor_lim, np.array([195, 195, 195]), np.array([255, 255, 255]))
            # Invierte la máscara para tener una máscara de los colores que quieres incluir
            mascara_colores = cv2.bitwise_not(mascara_excluir)

            # Usa la máscara para filtrar los píxeles de la imagen
            region_filtrada = cv2.bitwise_and(region_alrededor_lim, region_alrededor_lim, mask=mascara_colores)

            # Calcula el promedio de color solo de los píxeles filtrados
            pixels_sum = np.sum(region_filtrada, axis=(0, 1))
            pixels_count = cv2.countNonZero(mascara_colores)
            if pixels_count > 0:
                promedio_color_lim = pixels_sum / pixels_count
            else:
                promedio_color_lim = cv2.mean(region_alrededor_lim)[:3]
            
            promedio_color_lim_enteros = tuple(int(x) for x in promedio_color_lim)
            area_interseccion = poligono_lim.intersection(poligono_tra).area
            area_poligono_lim = poligono_lim.area
            porcentaje_interseccion = (area_interseccion / area_poligono_lim) * 100
            if poligono_lim.intersects(poligono_tra) and porcentaje_interseccion > 10:
                if tipo_limpieza == "Limpieza básica (B/N)":
                    self.text_image_processor.aplicar_relleno_solido(self.formato_manga, tipo_limpieza, coordenadas_caja_lim, promedio_color_lim, area_gris_lim)
                else: 
                    if self.app_window.rb_parrafo.isChecked():
                        bubble_detector = BubbleDetector(area_texto_lim)
                        mascara_area, _, _ = bubble_detector.canny_flood()
                    else:
                        mascara_area = self.text_image_processor.obtener_mascara_texto(self.formato_manga, tipo_limpieza, caja_lim, promedio_color_lim, area_gris_lim)
                    
                    self.mascara_global[y_lim:y_lim+h_lim, x_lim:x_lim+w_lim] = cv2.bitwise_or(mascara_area, self.mascara_global[y_lim:y_lim+h_lim, x_lim:x_lim+w_lim])  
        if tipo_limpieza == "Limpieza con transparencia":
            assert self.text_image_processor.imagen_con_alpha.shape[:2] == self.mascara_global.shape, "Imagen y máscara deben tener el mismo tamaño"
            self.text_image_processor.imagen_con_alpha[self.mascara_global == 255, 3] = 0
        elif  tipo_limpieza != "Limpieza básica (B/N)":
            self.text_image_processor.aplicar_inpainting(self.formato_manga, tipo_limpieza, self.mascara_global)
   
    def traducir_manga(self):
        for diccionario in self.valores_traduccion:
            self.text_image_processor.dibujar_texto(**diccionario)