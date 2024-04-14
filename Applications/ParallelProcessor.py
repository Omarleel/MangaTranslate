import torch.multiprocessing as mp

class ParallelProcessor:
    def __init__(self, num_processes = 4):
        self.num_processes = num_processes
        self.pool = mp.Pool(processes=num_processes)

    def dividir_imagenes_en_lotes(self, imagenes):
        # Divide las imágenes en lotes basados en el número de procesos
        batch_size = self.num_processes
        lotes = [imagenes[i:i + batch_size] for i in range(0, len(imagenes), batch_size)]
        return lotes
    
    def procesar_imagenes_en_paralelo(self, imagenes, process_func):
        try:
            # Procesa las imágenes en paralelo utilizando map_async para manejar excepciones
            resultados = self.pool.map_async(process_func, imagenes)
            # Espera a que todos los procesos completen y obtiene los resultados
            resultados = resultados.get()
            return resultados
        except Exception as e:
            # Captura cualquier excepción y la imprime
            print(f"Error al procesar imágenes en paralelo: {e}")
            return None