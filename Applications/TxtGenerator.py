class TxtGenerator:
    def __init__(self):
        self.contenido = []

    def agregar_linea(self, linea):
        self.contenido.append(linea)

    def guardar_en_archivo(self, nombre_archivo):
        with open(nombre_archivo, 'w', encoding='utf-8') as archivo:
            archivo.write('\n'.join(map(str, self.contenido)))