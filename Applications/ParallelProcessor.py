import torch.multiprocessing as mp

class ParallelProcessor:
    def __init__(self):
         mp.set_start_method('spawn', force=True)
         
    def procesar_en_paralelo(self, lista_imagenes, process_func, batch_size = 4):
        try:
            # Dividir las imágenes en lotes para procesamiento paralelo
            lotes_imagenes =  [lista_imagenes[i:i+batch_size] for i in range(0, len(lista_imagenes), batch_size)]
            num_processes = len(lotes_imagenes)
            processes = []
            for i in range(num_processes):
                # Seleccionar un lote de imágenes para cada proceso
                lote = lotes_imagenes[i]
                p = mp.Process(target=process_func, args=(lote,), daemon=True)
                p.start()
                processes.append(p)
            for p in processes:
                p.join()
            return True
        except Exception as e:
            # Captura cualquier excepción y la imprime
            print(f"Error al procesar imágenes en paralelo: {e}")
            return False