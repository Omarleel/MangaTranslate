# MangaTranslate - Documentación del programa

## Introducción
MangaTranslate es una herramienta diseñada para los apasionados del manga que buscan simplificar y optimizar el proceso de limpieza y traducción de mangas. Utilizando tecnología OCR (Optical Character Recognition), esta herramienta detecta automáticamente el texto dentro de los mangas escaneados y proporciona funcionalidades para traducir y limpiar las páginas, puede servir como apoyo a los grupos de scanlation.

## Características
- Procesamiento por Carpetas: Este sistema facilita el procesamiento de múltiples imágenes al permitir al usuario tanto seleccionar como especificar manualmente la ruta de la carpeta que alberga las imágenes destinadas a ser procesadas. Cabe destacar que se admiten formatos tales como .jpg, .png, .jpeg y .bmp. Adicionalmente, si se dispone de un enlace hacia un archivo .zip en Google Drive, el programa es capaz de descargarlo y descomprimirlo automáticamente para acceder a las imágenes contenidas.
- Detección Automática de Texto: Utiliza avanzados algoritmos OCR para identificar texto en páginas de manga, independientemente del estilo de dibujo o de letra.
- Limpieza de Páginas: Herramienta incorporada para eliminar los textos en las páginas.
- Camuflaje Avanzado: Camufla los textos en fondos de páginas a color, ya sean irregulares o no.
- Traducción Precisa con Google: Utiliza la potencia del GoogleTranslator de deep_translator para adaptar el manga a tu idioma preferido con alta fidelidad. Admite múltiples idiomas, entre ellos: japonés, inglés, español, coreano y chino.
- Interfaz Amigable: Diseñada tanto para novatos como para expertos en scanlation, ofreciendo una experiencia de usuario intuitiva y eficaz.
- Almacenamiento y Organización de Imágenes Procesadas: Tras su procesamiento, todas las imágenes son almacenadas en la carpeta "Outputs". Para facilitar la identificación y posterior consulta, las imágenes se organizan y clasifican en subcarpetas según la acción llevada a cabo sobre ellas, ya sea "Limpieza" o "Traducción".
- Exportación de Datos en Formato JSON: Para un análisis posterior o para usos avanzados, el sistema puede generar archivos .json estructurados que contienen las transcripciones y traducciones de las páginas procesadas. Este formato estructurado facilita la integración con otras aplicaciones o para realizar un seguimiento detallado del contenido procesado. 

##  Requerimientos
Antes de utilizar MangaTranslate, asegúrate de tener instalados los siguientes requisitos o instalarlos desde requirements.txt:
- Python 3.10.10
- **CUDA**: Esencial para el funcionamiento de algunas bibliotecas OCR que requieren procesamiento en GPU.
- OpenCV: Una biblioteca de procesamiento de imágenes y visión por computadora.
- EasyOCR: Una biblioteca para el reconocimiento óptico de caracteres (OCR) fácil de usar.
- Manga-OCR: Una biblioteca para el reconocimiento óptico de caracteres (OCR) especializada en mangas.
- PaddleOCR: Una biblioteca de OCR basada en PaddlePaddle que admite varios idiomas.
- Deep_Translator: Una biblioteca flexible, gratuita e ilimitada para traducir entre diferentes idiomas de forma sencilla utilizando varios traductores.
- Pillow: Una biblioteca para manipulación de imágenes en Python.
- Shapely: Una biblioteca de Python para el procesamiento y análisis de geometría.
- Gdown: Una herramienta y biblioteca de Python para descargar archivos y datasets de Google Drive.
- Pydrive: Una biblioteca de Python que envuelve la API de Google Drive, facilitando las operaciones de carga y descarga de archivos.

## Dependencias Adicionales
Para la correcta ejecución de este proyecto en entornos como Google Colab, se requiere la instalación de ciertas dependencias adicionales. A continuación, se describen los pasos:
1. Descarga e instala `libssl1.1`:
```bash
wget http://archive.ubuntu.com/ubuntu/pool/main/o/openssl/libssl1.1_1.1.0g-2ubuntu4_amd64.deb
sudo dpkg -i libssl1.1_1.1.0g-2ubuntu4_amd64.deb
```

## Instalación de CUDA compatible con Torch
Ejecuta los siguientes comandos:
```bash
# Desinstala cualquier versión de Torch que tengas
pip uninstall torch torchvision torchaudio
# Limpia la caché de pip para evitar conflictos
pip cache purge
# Instala la versión específica de Torch compatible con CUDA 12.1:
pip install torch==2.1.0+cu121 torchvision==0.16.0+cu121 --extra-index-url https://download.pytorch.org/whl/cu121
```

## Contribuciones
Considero que este proyecto aún se puede mejorar bastante, me encantaría que formes parte. Si encuentras algún bug, tienes alguna sugerencia o deseas añadir una nueva funcionalidad, ¡no dudes en abrir un Issue o enviar un Pull Request!

## Conclusión
MangaTranslate es un esfuerzo por combinar tecnologías avanzadas de OCR con la creciente demanda de herramientas eficientes para la traducción y adaptación del manga. Habiendo considerado la integralidad y precisión en la traducción, así como la conservación estética de las páginas, esta herramienta se posiciona como una solución esencial para aquellos involucrados en el mundo del scanlation. Invitamos a la comunidad de GitHub a probar, evaluar y contribuir a este proyecto, garantizando su adaptabilidad y relevancia a largo plazo.

## Pruebas
Para correr el programa, puedes ejecutar el siguiente conjunto de comandos:
```bash
# Clonar el repositorio y acceder a la carpeta del programa
git clone https://github.com/Omarleel/MangaTranslate
# Accede al proyecto
cd MangaTranslate
# Instala los requerimientos
pip install -r requirements/requirements.txt
# Ejecutar el script
py MangaTranslate.py
```
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1c9DtEwrNOv1Xkt4ZrVkKCtxd2MhXDMKY?usp=sharing)

## Interfaz gráfica en Windows
![GUI_Windows](https://github.com/Omarleel/MangaTranslate/blob/master/Assets/gui_windows.jpg)

## Resultados
Blanco y negro:
Original             |  Traducción          |  Limpieza
:-------------------------:|:-------------------------:|:-------------------------:
![Manga_Japonés](https://github.com/Omarleel/MangaTranslate/blob/master/Assets/Examples/manga_bn_ja.jpg)  |  ![Manga_Traducido](https://github.com/Omarleel/MangaTranslate/blob/master/Assets/Examples/traduccion_bn_es.jpg) | ![Manga_Limpio](https://github.com/Omarleel/MangaTranslate/blob/master/Assets/Examples/limpieza_bn.jpg)

Color:
Original             |  Traducción          |  Limpieza
:-------------------------:|:-------------------------:|:-------------------------:
![Manga_Japonés](https://github.com/Omarleel/MangaTranslate/blob/master/Assets/Examples/manga_color_ja.jpg)  |  ![Manga_Traducido](https://github.com/Omarleel/MangaTranslate/blob/master/Assets/Examples/traduccion_color_es.jpg) | ![Manga_Limpio](https://github.com/Omarleel/MangaTranslate/blob/master/Assets/Examples/limpieza_color.jpg)

## Créditos
MangaTranslate utiliza las siguientes bibliotecas y recursos:

- [easyocr](https://github.com/JaidedAI/EasyOCR): Para el reconocimiento óptico de caracteres en general para la limpieza.
- [manga-ocr](https://github.com/kha-white/manga-ocr): Para el reconocimiento óptico de caracteres en japonés.
- [paddleocr](https://github.com/PaddlePaddle/PaddleOCR): Para el reconocimiento óptico de caracteres en idiomas inglés, coreano y chino.
- [deep_translator](https://github.com/prataffel/deep_translator): Para la traducción automática.
- [shapely](https://github.com/Toblerity/Shapely): Para el procesamiento de geometría.
- [lama](https://github.com/advimman/lama): Para la técnica avanzada de inpainting.

Se agradece a los desarrolladores de estas bibliotecas por sus contribuciones.
