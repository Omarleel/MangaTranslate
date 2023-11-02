'''EJECUTAR EL PROGRAMA EN GOOGLE COLAB '''
#@title <font color='#018ada'>Interfaz MangaTranslate</font> { display-mode: "form" }
# from Applications.GoogleDriveManager import GoogleDriveManager
# from Widgets.AppColab import AppColab
# class MangaTranslate:
#     def __init__(self):
#         self.drive_manager = GoogleDriveManager()
#         self.app_colab = AppColab(self.drive_manager)
#         self.app_colab.crear_widgets()

   
# MangaTranslate = MangaTranslate()

'''EJECUTAR EL PROGRAMA EN ENTORNOS DE ESCRITORIO '''
from Widgets.AppWindow import AppWindow
from Applications.FileManager import FileManager
from PyQt5.QtWidgets import QApplication
import sys

class MangaTranslate:
    def __init__(self):
        self.file_manager = FileManager()
        self.app_window = AppWindow(self.file_manager)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    MangaTranslate = MangaTranslate()
    sys.exit(app.exec_())