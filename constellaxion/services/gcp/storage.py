import os
import gcsfs
from watchdog.events import FileSystemEventHandler

class GCSUploaderHandler(FileSystemEventHandler):
    def __init__(self, local_dir, gcs_dir):
        self.local_dir = local_dir
        self.gcs_dir = gcs_dir
        self.fs = gcsfs.GCSFileSystem()

    def on_modified(self, event):
        if not event.is_directory:
            self.upload_file(event.src_path)

    def on_created(self, event):
        if not event.is_directory:
            self.upload_file(event.src_path)

    def upload_file(self, file_path):
        relative_path = os.path.relpath(file_path, self.local_dir)
        gcs_path = os.path.join(self.gcs_dir, relative_path)
        
        try:
            with open(file_path, "rb") as f:
                with self.fs.open(gcs_path, "wb") as gcs_file:
                    gcs_file.write(f.read())
            print(f"✅ Uploaded: {relative_path} to {gcs_path}")
        except Exception as e:
            print(f"❌ Failed to upload {relative_path}: {e}")