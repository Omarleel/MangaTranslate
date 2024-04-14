import torch.multiprocessing as mp

class ParallelProcessor:
    def __init__(self, batch_size=4):
        self.batch_size = batch_size
    def procesar_imagenes_en_paralelo(self, lista_imagenes, process_func):
        try:
            # Dividir las imágenes en lotes para procesamiento paralelo
            lotes_imagenes = [lista_imagenes[i:i + self.batch_size] for i in range(0, len(lista_imagenes), self.batch_size)]
            
            # Asegurarse de que el número de procesos no sea mayor que el número de lotes
            num_processes =  len(lotes_imagenes)
            processes = []
            for i in range(num_processes):
                # Seleccionar un lote de imágenes para cada proceso
                lote = lotes_imagenes[i]
                p = mp.Process(target=process_func, args=(lote,))
                p.start()
                processes.append(p)
            for p in processes:
                p.join()
            return True
        except Exception as e:
            # Captura cualquier excepción y la imprime
            print(f"Error al procesar imágenes en paralelo: {e}")
            return False
