import sys
import os
import threading
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QComboBox, QLabel, QRadioButton, QButtonGroup, QLineEdit, QPushButton, QProgressBar, QFileDialog, QDesktopWidget, QHBoxLayout
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from Applications.ProcessorWindows import Processor
from Applications.Utilities import Utilities
from Utils.Constantes import RUTA_ACTUAL, RUTA_LOCAL_SALIDA

class AppWindow(QWidget):
    imagen_procesada_signal = pyqtSignal(int, str, int)
    def __init__(self, file_manager):
        super().__init__()
        self.ruta_pdf_resultante = None
        self.file_manager = file_manager
        self.utilities = Utilities()
        self.utilities.download_font_windows()
        self.utilities.download_lama_model_windows()
        self.ruta_carpeta_entrada = None
        self.ruta_carpeta_salida = None
        self.nombre_carpeta = None
        self.initUI()
        self.centrar_ventana()
        self.imagen_procesada_signal.connect(self.on_imagen_procesada)
        self.processor = Processor(self)

    def initUI(self):
        layout = QVBoxLayout()
        self.setWindowTitle("MangaTranslate (by Omarleel)")
        self.setGeometry(0, 0, 580, 480)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMaximizeButtonHint)
        
        self.lbl_tipo_limpieza = QLabel("Tipo de limpieza:", self)
        layout.addWidget(self.lbl_tipo_limpieza)
        self.dropdown_limpieza = QComboBox(self)
        self.dropdown_limpieza.addItems(["Auto", "Limpieza básica (B/N)", "Limpieza con transparencia", "Limpieza a color (Lama)", "Limpieza a color (NS)", "Limpieza a color (Telea)"])
        layout.addWidget(self.dropdown_limpieza)

        self.lbl_tipo_deteccion_texto = QLabel("Tipo de detección de texto:", self)
        layout.addWidget(self.lbl_tipo_deteccion_texto)

        self.opcion_analisis = QButtonGroup(self)
        self.rb_palabra = QRadioButton("Por palabra", self)
        self.rb_parrafo = QRadioButton("Por párrafo", self)

        self.opcion_analisis.addButton(self.rb_palabra)
        self.opcion_analisis.addButton(self.rb_parrafo)

        radio_layout = QHBoxLayout()
        radio_layout.addWidget(self.rb_palabra)
        radio_layout.addWidget(self.rb_parrafo)

        layout.addLayout(radio_layout)

        self.rb_palabra.setChecked(True)

        self.lbl_accion = QLabel("Acción:", self)
        layout.addWidget(self.lbl_accion)
        self.opcion_accion = QComboBox()
        self.opcion_accion.addItems(["Solo limpiar", "Solo traducir" ,"Limpiar y traducir"])
        self.opcion_accion.setCurrentText("Limpiar y traducir")
        layout.addWidget(self.opcion_accion)
        
        self.lbl_idioma_entrada = QLabel("Traducir del:", self)
        layout.addWidget(self.lbl_idioma_entrada)

        self.dropdown_idioma_entrada = QComboBox(self)
        self.dropdown_idioma_entrada.addItems(["Japonés", "Koreano", "Chino", "Inglés"])
        layout.addWidget(self.dropdown_idioma_entrada)

        self.lbl_idioma_salida = QLabel("Traducir al:", self)
        layout.addWidget(self.lbl_idioma_salida)

        self.dropdown_idioma_salida = QComboBox(self)
        self.dropdown_idioma_salida.addItems(["Español", "Inglés", "Portugués", "Francés", "Italiano"])
        layout.addWidget(self.dropdown_idioma_salida)

        self.lbl_densidad_globos = QLabel("Densidad de globos de texto:", self)
        layout.addWidget(self.lbl_densidad_globos)

        self.opcion_densidad_globos = QButtonGroup(self)
        self.rb_muy_denso = QRadioButton("Muy denso", self)
        self.rb_poco_denso = QRadioButton("Poco denso", self)

        self.opcion_densidad_globos.addButton(self.rb_muy_denso)
        self.opcion_densidad_globos.addButton(self.rb_poco_denso)

        densidad_layout = QHBoxLayout()
        densidad_layout.addWidget(self.rb_muy_denso)
        densidad_layout.addWidget(self.rb_poco_denso)

        layout.addLayout(densidad_layout)

        self.rb_muy_denso.setChecked(True)

        self.textbox_ruta_carpeta = CustomLineEdit(self)
        self.textbox_ruta_carpeta.setPlaceholderText("Ingrese la ruta de la carpeta o el link de Google Drive...")
        layout.addWidget(self.textbox_ruta_carpeta)
        # Conectar la señal keyPressed al slot (método) handleKeyPress
        self.textbox_ruta_carpeta.keyPressed.connect(self.handleKeyPress)

        self.boton_seleccionar_carpeta = QPushButton("Seleccionar", self)
        self.boton_seleccionar_carpeta.clicked.connect(self.seleccionar_carpeta)
        layout.addWidget(self.boton_seleccionar_carpeta)
        
        self.boton_comenzar_procesamiento = QPushButton("Comenzar procesamiento", self)
        self.boton_comenzar_procesamiento.clicked.connect(self.comenzar_procesamiento)
        layout.addWidget(self.boton_comenzar_procesamiento)
        self.boton_comenzar_procesamiento.setEnabled(False)

        self.boton_cancelar_procesamiento = QPushButton("Cancelar procesamiento", self)
        self.boton_cancelar_procesamiento.clicked.connect(self.cancelar_procesamiento)
        layout.addWidget(self.boton_cancelar_procesamiento)
        self.boton_cancelar_procesamiento.setEnabled(False)

        hlayout = QHBoxLayout()
        self.etiqueta_info_carga = QLabel("Cargando: -", self)
        hlayout.addWidget(self.etiqueta_info_carga)
        hlayout.addStretch(1)
        self.etiqueta_cantidad_imagenes = QLabel("Cantidad de imágenes: -", self)
        hlayout.addWidget(self.etiqueta_cantidad_imagenes)
        layout.addLayout(hlayout)

        self.progressbar_carga = QProgressBar(self)
        layout.addWidget(self.progressbar_carga)

        self.etiqueta_estado_procesamiento = QLabel("Procesando: -", self)
        layout.addWidget(self.etiqueta_estado_procesamiento)

        self.progressbar_procesamiento = QProgressBar(self)
        layout.addWidget(self.progressbar_procesamiento)

        self.boton_abrir_pdf = QPushButton("Abrir archivo pdf", self)
        self.boton_abrir_pdf.clicked.connect(lambda: self.utilities.abrir_pdf(self.ruta_pdf_resultante))
        layout.addWidget(self.boton_abrir_pdf)
        self.boton_abrir_pdf.setDisabled(True)
        
        self.setLayout(layout)
        self.show()
        
    def centrar_ventana(self):
        frame_geo = self.frameGeometry()  # Obtiene un rectángulo con la geometría de la ventana
        centro_pantalla = QDesktopWidget().availableGeometry().center()  # Encuentra el centro de la pantalla
        frame_geo.moveCenter(centro_pantalla)  # Mueve el centro del rectángulo a la posición del centro de la pantalla
        self.move(frame_geo.topLeft())

    def seleccionar_carpeta(self, ruta_carpeta_entrada = None):
        if ruta_carpeta_entrada is None or ruta_carpeta_entrada == False:
            ruta_carpeta_entrada = QFileDialog.getExistingDirectory(self, "Selecciona una carpeta")
            # Si es una cadena vacía o None, regresamos.
            if not ruta_carpeta_entrada:
                return
        self.desactivar_botones_y_progressbar()
        self.resetear_valores_iniciales()
        nombre_carpeta = os.path.basename(ruta_carpeta_entrada)
        
        archivos = os.listdir(ruta_carpeta_entrada)
        archivos_imagen = [
            archivo for archivo in archivos if archivo.lower().endswith(('.jpg', '.png', '.jpeg', '.bmp'))
        ]
        self.etiqueta_info_carga.setText("Cargando: Completado")
        self.progressbar_carga.setValue(100)
        cantidad_imagenes = len(archivos_imagen)
        self.etiqueta_cantidad_imagenes.setText(f"Cantidad de imágenes: {cantidad_imagenes}")
        
        self.ruta_carpeta_entrada = ruta_carpeta_entrada
        self.ruta_carpeta_salida = os.path.join(RUTA_ACTUAL, RUTA_LOCAL_SALIDA, nombre_carpeta)
        self.nombre_carpeta = nombre_carpeta
        self.boton_comenzar_procesamiento.setEnabled(True)
        self.textbox_ruta_carpeta.clear()
        self.textbox_ruta_carpeta.insert(ruta_carpeta_entrada)
    
    def activar_btn_pdf(self):
        self.boton_abrir_pdf.setEnabled(True)
    def desactivar_btn_pdf(self):
        self.boton_abrir_pdf.setEnabled(False)

    def set_ruta_pdf_resultante(self, ruta_pdf_resultante):
        self.ruta_pdf_resultante = ruta_pdf_resultante
        
    def desactivar_botones_y_progressbar(self):
        self.boton_comenzar_procesamiento.setEnabled(False)
        self.desactivar_btn_pdf()
        self.progressbar_carga.setValue(0)
        self.progressbar_procesamiento.setValue(0)
        self.etiqueta_info_carga.setText("Cargando: -")
        self.etiqueta_cantidad_imagenes.setText("Cantidad de imágenes: -")
        self.etiqueta_estado_procesamiento.setText("Procesando: -")

    def resetear_valores_iniciales(self):
        self.progressbar_carga.setValue(0)
        self.progressbar_procesamiento.setValue(0)

    def comenzar_procesamiento(self):
        if len(self.textbox_ruta_carpeta.text()) > 0:
            self.thread = ProcessingThread(self.processor, self.ruta_carpeta_entrada, self.ruta_carpeta_salida, self.nombre_carpeta)
            self.thread.imagen_procesada_signal.connect(self.on_imagen_procesada)
            self.thread.start()
            self.boton_cancelar_procesamiento.setEnabled(True)
            self.boton_comenzar_procesamiento.setEnabled(False)

    def cancelar_procesamiento(self):
        if hasattr(self, 'thread'):
            self.thread.stop()
            self.boton_cancelar_procesamiento.setEnabled(False)
            self.boton_comenzar_procesamiento.setEnabled(True)

    def on_imagen_procesada(self, cantidad_imagenes, nombre_imagen, valor_progreso):
        self.etiqueta_cantidad_imagenes.setText(f"Cantidad de imágenes: {cantidad_imagenes}")
        self.etiqueta_estado_procesamiento.setText(f"Procesando: {nombre_imagen}")
        self.progressbar_procesamiento.setValue(valor_progreso)
    
    def on_download_completed(self, ruta_carpeta_entrada):
        if ruta_carpeta_entrada:
            self.textbox_ruta_carpeta.setText(ruta_carpeta_entrada)
            self.seleccionar_carpeta(ruta_carpeta_entrada)

    def handleKeyPress(self):
        texto_digitado = self.textbox_ruta_carpeta.text()
        if len(texto_digitado) == 0:
            self.boton_comenzar_procesamiento.setEnabled(False)
        elif "https://drive.google.com/file/d/" in texto_digitado and len(texto_digitado) >= 65:
            self.download_thread = DownloadThread(self.utilities, texto_digitado)
            self.download_thread.download_completed_signal.connect(self.on_download_completed)
            self.download_thread.start()

        
class CustomLineEdit(QLineEdit):
    keyPressed = pyqtSignal()
    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        self.keyPressed.emit()

class DownloadThread(QThread):
    download_completed_signal = pyqtSignal(str)

    def __init__(self, utilities, url_drive):
        super().__init__()
        self.utilities = utilities
        self.url_drive = url_drive

    def run(self):
        try:
            ruta_carpeta_entrada = self.utilities.descargar_y_extraer_zip(self.url_drive)
            self.download_completed_signal.emit(ruta_carpeta_entrada)
        except Exception as e:
            print(f"Error en DownloadThread: {e}")
            self.download_completed_signal.emit(None)

class ProcessingThread(QThread):
    imagen_procesada_signal = pyqtSignal(int, str, int)
    
    def __init__(self, processor, ruta_carpeta_entrada, ruta_carpeta_salida, nombre_carpeta):
        super().__init__()
        self.processor = processor
        self.ruta_carpeta_entrada = ruta_carpeta_entrada
        self.ruta_carpeta_salida = ruta_carpeta_salida
        self.nombre_carpeta = nombre_carpeta
        self._is_running = threading.Event()
        self._is_running.set()

    def run(self):
        self.processor.procesar_imagenes(self.ruta_carpeta_entrada, self.ruta_carpeta_salida, self.nombre_carpeta, self._is_running)

    def stop(self):
        self._is_running.clear()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = AppWindow(file_manager=None)  # Aquí debes proporcionar el drive_manager adecuado
    sys.exit(app.exec_())
