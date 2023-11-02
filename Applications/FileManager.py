import os
import shutil

class FileManager:

    def __init__(self, base_path="."):
        self.base_path = os.path.abspath(base_path)

    def _get_full_path(self, path):
        return os.path.join(self.base_path, path)

    def create_folder(self, folder_path):
        full_path = self._get_full_path(folder_path)
        try:
            os.makedirs(full_path, exist_ok=True)
            return full_path
        except Exception as e:
            print(f"Error: {e}")
            return None

    def upload_file(self, source_file_path, destination_folder, destination_file_name=None):
        destination_full_path = self._get_full_path(destination_folder)
        try:
            if not os.path.exists(destination_full_path):
                self.create_folder(destination_folder)

            if destination_file_name:
                destination = os.path.join(destination_full_path, destination_file_name)
            else:
                destination = os.path.join(destination_full_path, os.path.basename(source_file_path))

            shutil.copy2(source_file_path, destination)
            return destination
        except Exception as e:
            print(f"Error: {e}")
            return None

    def delete_folder(self, folder_path):
        full_path = self._get_full_path(folder_path)
        try:
            if os.path.exists(full_path):
                shutil.rmtree(full_path)
                return True
            else:
                print(f"Folder {full_path} does not exist!")
                return False
        except Exception as e:
            print(f"Error: {e}")
            return False

    def delete_file(self, file_path):
        full_path = self._get_full_path(file_path)
        try:
            if os.path.exists(full_path) and os.path.isfile(full_path):
                os.remove(full_path)
                return True
            else:
                print(f"File {full_path} does not exist!")
                return False
        except Exception as e:
            print(f"Error: {e}")
            return False

    def download_folder(self, source_folder_path, destination_path):
        source_full_path = self._get_full_path(source_folder_path)
        try:
            if not os.path.exists(destination_path):
                os.makedirs(destination_path, exist_ok=True)

            destination = os.path.join(destination_path, os.path.basename(source_full_path))
            shutil.copytree(source_full_path, destination)
            return destination
        except Exception as e:
            print(f"Error: {e}")
            return None

    def download_file(self, source_file_path, destination_path):
        source_full_path = self._get_full_path(source_file_path)
        try:
            if not os.path.exists(destination_path):
                os.makedirs(destination_path, exist_ok=True)

            destination = os.path.join(destination_path, os.path.basename(source_full_path))
            shutil.copy2(source_full_path, destination)
            return destination
        except Exception as e:
            print(f"Error: {e}")
            return None