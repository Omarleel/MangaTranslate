
import sys
import os
sys.path.append(os.path.dirname(os.getcwd()))
from Utils.Constantes import RUTA_REMOTA, RUTA_LOCAL_ZIPS
from pydrive2.auth import GoogleAuth
from google.colab import auth
from pydrive2.drive import GoogleDrive
from oauth2client.client import GoogleCredentials
from urllib.parse import urlparse, parse_qs
from shutil import unpack_archive

class GoogleDriveManager:
    def __init__(self):
        auth.authenticate_user()
        gauth = GoogleAuth()
        gauth.credentials = GoogleCredentials.get_application_default()
        self.drive = GoogleDrive(gauth)
 
    def get_folder_or_file_id(self, name, parent_folder_id=None, is_folder=True):
        try:
            if parent_folder_id is None:
                parent_folder_id = "root"  # Usa "root" para referirte a la raíz de Google Drive
                
            query = f"'{parent_folder_id}' in parents and trashed=false"
            query += " and mimeType = 'application/vnd.google-apps.folder'" if is_folder else " and mimeType != 'application/vnd.google-apps.folder'"

            folder_list = self.drive.ListFile({'q': query}).GetList()
            
            for item in folder_list:
                if item['title'] == name:
                    return item['id']
            
            return None
        except Exception as e:
            return None
              
    def create_folder(self, folder_name, parent_folder_id=None):
        try:
            # Si el nombre de la carpeta comienza con '/', elimina ese carácter
            if folder_name.startswith('/'):
                folder_name = folder_name[1:]

            # Filtra las cadenas vacías después de dividir la ruta
            parts = [part for part in folder_name.split('/') if part]

            current_parent_id = parent_folder_id
            for part_name in parts:
                # Comprobar si ya existe una carpeta con el nombre de la parte actual
                existing_folder_id = self.get_folder_or_file_id(part_name, current_parent_id, is_folder=True)
                
                if existing_folder_id:
                    current_parent_id = existing_folder_id  # Si la carpeta ya existe, usamos su ID como padre para la siguiente parte
                else:
                    folder_metadata = {
                        'title': part_name,
                        'mimeType': 'application/vnd.google-apps.folder'
                    }

                    if current_parent_id:
                        folder_metadata['parents'] = [{'id': current_parent_id}]

                    new_folder = self.drive.CreateFile(folder_metadata)
                    new_folder.Upload()
                    current_parent_id = new_folder['id']  # Usar el ID de la nueva carpeta como padre para la siguiente parte
            
            return current_parent_id  # Retorna el ID de la última carpeta creada o encontrada
        except Exception as e:
            print(f"Error: {e}")
            return None
 
    def upload_file(self, local_file_path, folder_name, remote_file_name=None):
        try:
            # Si el nombre de la carpeta comienza con '/', elimina ese carácter
            if folder_name.startswith('/'):
                folder_name = folder_name[1:]

            # Filtra las cadenas vacías después de dividir la ruta
            parts = [part for part in folder_name.split('/') if part]

            current_parent_id = None
            for part_name in parts:
                # Comprobar si ya existe una carpeta con el nombre de la parte actual
                existing_folder_id = self.get_folder_or_file_id(part_name, current_parent_id, is_folder=True)
                
                if existing_folder_id:
                    current_parent_id = existing_folder_id  # Si la carpeta ya existe, usamos su ID como padre para la siguiente parte
                else:
                    folder_metadata = {
                        'title': part_name,
                        'mimeType': 'application/vnd.google-apps.folder'
                    }

                    if current_parent_id:
                        folder_metadata['parents'] = [{'id': current_parent_id}]

                    new_folder = self.drive.CreateFile(folder_metadata)
                    new_folder.Upload()
                    current_parent_id = new_folder['id']  # Usar el ID de la nueva carpeta como padre para la siguiente parte

            # Subir el archivo a la carpeta de destino
            remote_file = self.drive.CreateFile({'title': remote_file_name or os.path.basename(local_file_path), 'parents': [{'id': current_parent_id}]})
            remote_file.SetContentFile(local_file_path)
            remote_file.Upload()
            
            return current_parent_id
        except Exception as e:
            print(f"Error: {e}")
        
    def delete_folder(self, folder_id):
        try:
            # Obtén la lista de archivos dentro de la carpeta por su ID
            folder = self.drive.CreateFile({'id': folder_id})
            archivo_list = self.drive.ListFile({'q': f"'{folder_id}' in parents and trashed=false"}).GetList()

            # Elimina cada archivo en la carpeta
            for archivo in archivo_list:
                file_id = archivo['id']
                file_to_delete = self.drive.CreateFile({'id': file_id})
                file_to_delete.Trash()

            # Elimina la carpeta
            folder.Trash()

            return True
        except Exception as e:
            return False
        
    def delete_file(self, file_id):
        try:
            file_to_delete = self.drive.CreateFile({'id': file_id})
            file_to_delete.Trash()
            return True
        except Exception as e:
            return False

    def download_folder_by_link(self, folder_link, local_folder_path = None):
        formato_link_carpeta_compartida = "https://drive.google.com/drive/folders/"
        formato_link_archivo_compartido = "https://drive.google.com/file/d/"
        try:
            if folder_link.startswith(formato_link_carpeta_compartida):
                parsed_url = urlparse(folder_link)
                query_params = parse_qs(parsed_url.query)
                folder_id = None

                if 'folders' in parsed_url.path:
                    folder_id = parsed_url.path.split('/')[-1]
                elif 'id' in query_params:
                    folder_id = query_params['id'][0]

                if folder_id:
                    # Obtiene la lista de archivos dentro de la carpeta compartida por su ID
                    archivo_list = self.drive.ListFile({'q': f"'{folder_id}' in parents and trashed=false"}).GetList()

                    # Ruta local en Google Colab donde se descargarán los archivos
                    downloaded = self.drive.CreateFile({'id': folder_id})
                    nombre_carpeta = downloaded['title']
                    ruta_carpeta_entrada = os.path.join(local_folder_path or "/", nombre_carpeta)

                    # Crea la carpeta local si no existe
                    os.makedirs(ruta_carpeta_entrada, exist_ok=True)

                    # Descarga cada archivo en la carpeta local
                    for archivo in archivo_list:
                        file_id = archivo['id']
                        downloaded_file = self.drive.CreateFile({'id': file_id})
                        downloaded_file.GetContentFile(os.path.join(ruta_carpeta_entrada, archivo['title']))
                    ruta_carpeta_salida = os.path.join(RUTA_REMOTA, f"{nombre_carpeta}")
                    return nombre_carpeta, ruta_carpeta_entrada, ruta_carpeta_salida
                else:
                    return False

            elif folder_link.startswith(formato_link_archivo_compartido):
                ruta_zip_local = RUTA_LOCAL_ZIPS
                os.makedirs(ruta_zip_local, exist_ok=True)

                # Obtener id del archivo y descargar
                id_archivo = folder_link.split('/')[-2]
                downloaded = self.drive.CreateFile({'id': id_archivo})
                tipo_archivo = downloaded['fileExtension']
                
                if tipo_archivo == "zip":
                    nombre_real_archivo = downloaded['title']
                    ruta_archivo_descargado = os.path.join(ruta_zip_local, nombre_real_archivo)
                    downloaded.GetContentFile(ruta_archivo_descargado)
                    ruta_carpeta_entrada = ruta_archivo_descargado.replace(".zip", "")
                    nombre_real_archivo = nombre_real_archivo.replace(".zip", "")
                    os.makedirs(ruta_carpeta_entrada, exist_ok=True)
                    unpack_archive(ruta_archivo_descargado, ruta_carpeta_entrada, 'zip')
                    # Borrar el archivo ZIP después de extraer las imágenes
                    os.remove(ruta_archivo_descargado)
                    ruta_carpeta_salida =  os.path.join(RUTA_REMOTA, f"{nombre_real_archivo}")
                    return nombre_real_archivo, ruta_carpeta_entrada, ruta_carpeta_salida
                elif tipo_archivo == "ttf":
                    nombre_real_archivo = downloaded['title']
                    ruta_archivo_descargado = os.path.join(local_folder_path, nombre_real_archivo)
                    downloaded.GetContentFile(ruta_archivo_descargado)
                    return ruta_archivo_descargado
                elif tipo_archivo == "ckpt":
                    nombre_real_archivo = downloaded['title']
                    ruta_archivo_descargado = os.path.join(local_folder_path, nombre_real_archivo)
                    downloaded.GetContentFile(ruta_archivo_descargado)
                    return ruta_archivo_descargado
                else:
                    self.etiqueta_info_carga.value = "Error, no es un archivo válido."
                    return False
            else:
                 return False
                    
        except Exception as e:
            return False