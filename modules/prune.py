from concurrent.futures import ThreadPoolExecutor
from os import listdir, makedirs, path, replace, unlink
from threading import Lock, Thread
from time import sleep

from PIL import Image


class Prune:
    """
    Mirrors PNGs from a source directory into a target directory as metadata-free copies.
    """

    def __init__(self, source_dir: str, target_dir: str, max_workers: int):
        self._exclusive_lock = Lock()
        self._exec = ThreadPoolExecutor(max_workers)
        self._wait = set[str]()
        Thread(target=self._poll, args=(source_dir, target_dir), daemon=True).start()

    def _poll(self, source_dir: str, target_dir: str):
        while True:
            try:
                # Ensure source and target exist.
                makedirs(source_dir, exist_ok=True)
                makedirs(target_dir, exist_ok=True)

                # Read the source and target.
                sources = set(listdir(source_dir))
                targets = set(listdir(target_dir))

                # Queue new images.
                with self._exclusive_lock:
                    for name in sorted(sources):
                        if (
                            name.endswith(".png")
                            and name not in targets
                            and name not in self._wait
                        ):
                            self._wait.add(name)
                            self._exec.submit(self._prune, source_dir, target_dir, name)

                # Trash old images.
                for name in targets:
                    if name.endswith(".png") and name not in sources:
                        unlink(path.join(target_dir, name))
            except FileNotFoundError:
                continue
            finally:
                sleep(1)

    def _prune(self, source_dir: str, target_dir: str, name: str):
        source_file = path.join(source_dir, name)
        target_file = path.join(target_dir, name)
        output_file = f"{target_file}.tmp"

        try:
            while True:
                # Prune output image.
                try:
                    with Image.open(source_file) as image:
                        image.save(output_file, format="png", pnginfo=None)
                except FileNotFoundError:
                    break
                except Exception:
                    sleep(1)
                    continue

                # Atomic swap into place.
                replace(output_file, target_file)
                break
        finally:
            with self._exclusive_lock:
                self._wait.remove(name)
