import logging
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

logger = logging.getLogger(__name__)


class ImageDirectoryEventHandler(FileSystemEventHandler):
    def on_created(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        logger.info("image directory file created", extra={"path": event.src_path})


def create_observer(path: str | Path) -> Observer:
    observer = Observer()
    observer.schedule(ImageDirectoryEventHandler(), str(path), recursive=False)
    return observer
