import json

class JsonGenerator:
    def __init__(self):
        self.datos = {}

    def agregar_entrada(self, clave, valor):
        self.datos[clave] = valor

    def agregar_elemento_a_lista(self, clave, elemento):
        self.datos.setdefault(clave, []).append(elemento)

    def agregar_a_sublista(self, clave_lista, indice, clave_sublista, elemento_sublista):
        # Asegúrate de que la clave_lista ya es una lista en los datos
        if clave_lista not in self.datos or not isinstance(self.datos[clave_lista], list):
            raise ValueError(f"La clave '{clave_lista}' no existe o no es una lista.")
        
        # Expandir la lista principal si es necesario
        while len(self.datos[clave_lista]) <= indice:
            self.datos[clave_lista].append({})
        
        # Asegúrate de que el elemento específico es un diccionario
        if not isinstance(self.datos[clave_lista][indice], dict):
            raise ValueError(f"El elemento con índice {indice} no es un diccionario.")
        
        # Añadir o actualizar la sublista
        self.datos[clave_lista][indice].setdefault(clave_sublista, []).append(elemento_sublista)

    def guardar_en_archivo(self, nombre_archivo):
        with open(nombre_archivo, 'w', encoding='utf-8') as archivo:
            json.dump(self.datos, archivo, ensure_ascii=False, indent=4)