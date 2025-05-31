"""
This module provides a class for uploading files to a GCS bucket.
"""

import os
import threading
import time

import gcsfs
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class GCSUploaderHandler(FileSystemEventHandler):
    """
    A class that handles file system events and uploads them to a GCS bucket.
    """

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
        """Upload a file to a GCS bucket."""
        relative_path = os.path.relpath(file_path, self.local_dir)
        gcs_path = os.path.join(self.gcs_dir, relative_path)

        try:
            with open(file_path, "rb") as f:
                with self.fs.open(gcs_path, "wb") as gcs_file:
                    gcs_file.write(f.read())
            print(f"✅ Uploaded: {relative_path} to {gcs_path}")
        except Exception as e:
            print(f"❌ Failed to upload {relative_path}: {e}")

    def upload_directory(self, directory_path):
        """Upload a directory to a GCS bucket."""
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                self.upload_file(os.path.join(root, file))
            for directory in dirs:
                self.upload_directory(os.path.join(root, directory))


def start_gcs_sync(local_dir, gcs_dir):
    """Sync local directory to GCS bucket"""
    event_handler = GCSUploaderHandler(local_dir, gcs_dir)
    observer = Observer()
    observer.schedule(event_handler, path=local_dir, recursive=True)
    observer.start()
    print(f"🚀 Started syncing from {local_dir} to {gcs_dir}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


def start_gcs_sync_thread(local_dir, gcs_dir):
    """Start the GCS sync in a separate thread"""
    os.makedirs(local_dir, exist_ok=True)
    sync_thread = threading.Thread(
        target=start_gcs_sync, args=(local_dir, gcs_dir), daemon=True
    )
    sync_thread.start()
