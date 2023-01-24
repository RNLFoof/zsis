import functools
import hashlib
import os
import re
import sqlite3
import sys

import json5
from PIL import Image

from zsis.classes.SourcerSettings import SourcerSettings


class SourcerException(Exception):
    pass

class Sourcer:
    def __init__(self, settings: SourcerSettings, save_path="sources.db") -> None:
        self.save_path = save_path
        self.settings = settings
        self.con: sqlite3.Connection = None
        self.cursor: sqlite3.Cursor = None
        self._open_db()

    def __enter__(self) -> "Sourcer":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self._close_db()

    def _open_db(self) -> None:
        self.con = sqlite3.connect(self.save_path)
        self.cursor = self.con.cursor()
        # Ensure the table exists
        with open("zsis/json/db_definitions.json5", "rb") as f:
            for line in json5.load(f):
                try:
                    self.cursor.executescript(line)
                except sqlite3.OperationalError as e:
                    if re.match(r"table .+ already exists", str(e)):
                        continue
                    raise e

    def _close_db(self) -> None:
        try:
            self.con.commit()

            with sqlite3.connect('_backup'.join(os.path.splitext(self.save_path))) as backup_con:
                self.con.backup(backup_con)

            self.con.close()
        except sqlite3.ProgrammingError as e:
            print("OW")
            tb = sys.exc_info()[2]
            print(e.with_traceback(tb))

    # Generating hashes
    def gen_color_hash(self, full_path: str):
        full_path = polish_path(full_path)
        try:
            scale_x = self.settings.scale_x
            scale_y = self.settings.scale_y
            factor_divider = self.settings.factor_divider
            bw = self.settings.bw
            scaling = self.settings.scaling
            resample = self.settings.resample

            img = Image.open(full_path)
            if bw:
                img = img.convert("L")
            else:
                img = img.convert("RGB")
            img = img.resize((scale_x, scale_y), resample=resample)

            if bw:
                scale_count = 1
            else:
                scale_count = 3
            if scaling and scale_x * scale_y > 1:
                scale_high = [0] * scale_count
                scale_low = [9999] * scale_count
                imgdata = img.load()
                for x in range(img.size[0]):
                    for y in range(img.size[1]):
                        working = imgdata[x, y]
                        if bw:
                            scale_high[0] = max(working, scale_high[0])
                            scale_low[0] = min(working, scale_low[0])
                        else:
                            for n, z in enumerate(working):
                                scale_high[n] = max(z, scale_high[n])
                                scale_low[n] = min(z, scale_low[n])
            else:
                scale_high = [255] * scale_count
                scale_low = [0] * scale_count
            scaledif = []
            for x in range(scale_count):
                scaledif.append(max(scale_high[x] - scale_low[x], 0.001))

            img = list(img.split())
            for x in range(scale_count):
                img[x] = Image.eval(img[x],
                                    lambda y: min(
                                        math.floor(((y - scale_low[x]) / scaledif[x] * 255) / 255 * factor_divider),
                                        factor_divider))
            if bw:
                img = Image.merge("L", img)
            else:
                img = Image.merge("RGB", img)

            pixels = []
            imgload = img.load()
            for x in range(scale_x):
                for y in range(scale_y):
                    pixels.append(imgload[x, y])

            h = hashlib.md5()
            s = img.tobytes()

            h.update(s)
            h = h.hexdigest()

            return h
        except Image.UnidentifiedImageError as e:
            return b"fh___" + self.gen_file_hash(full_path)
        except Exception as e:
            print(full_path)
            raise e

    @classmethod
    def gen_file_hash(cls, full_path):
        if os.stat(full_path).st_size == 0:
            raise SourcerException("File is empty!")

        block_size = 65536

        img_hash = hashlib.sha256()
        with open(full_path, 'rb') as f:
            fb = f.read(block_size)
            if len(fb) == 0:
                raise SourcerException("File is empty!")
            while len(fb) > 0:
                img_hash.update(fb)
                fb = f.read(block_size)
        img_hash = img_hash.digest()
        return img_hash

    # DB IO
    def get_sourceable(self, full_path: str) -> tuple:
        full_path = polish_path(full_path)
        return self.cursor.execute('SELECT * FROM sourceable WHERE fullpath=?', (full_path,)).fetchone()

    def add_sourceable(self, full_path: str):
        """


        Parameters
        ----------
        full_path
        """
        full_path = polish_path(full_path)
        run_this = functools.partial(
            self.cursor.execute,
            'INSERT INTO sourceable (fullpath, filehash) VALUES (?,?)',
            (
                full_path,
                gen_file_hash(full_path)
            )
        )
        return ignore_unique_violation_of(run_this)

    def get_color_hash(self, full_path: str) -> tuple:
        return self.cursor.execute('SELECT * FROM colorhash WHERE fullpath=? AND settingsrepstr=?',
                                   (full_path, self.settings.rep_str)).fetchone()

    def add_color_hash(self, full_path: str):
        run_this = functools.partial(
            self.cursor.execute,
            'INSERT INTO colorhash (fullpath, colorhash, settingsrepstr) VALUES (?,?,?)',
            (
                full_path,
                self.gen_color_hash(full_path),
                self.settings.rep_str
            )
        )
        return ignore_unique_violation_of(run_this)

    def ensure_color_hash(self, full_path: str) -> tuple:
        color_hash = self.get_color_hash(full_path)
        if color_hash is None:
            self.add_color_hash(full_path)
            return self.get_color_hash(full_path)
        else:
            return color_hash

    def add_source(self, file_hash: bytes, source: str):
        run_this = functools.partial(
            self.cursor.execute,
            'INSERT INTO source (filehash, source) VALUES (?,?)',
            (
                file_hash,
                source
            )
        )
        return ignore_unique_violation_of(run_this)

    def catalog_file(self, path: str, sources: list[str], add_path_to_sources: bool,
                     _reporter: Optional[Reporter] = None) -> Reporter:
        """

        Parameters
        ----------
        _reporter
        sources
        path
        add_path_to_sources

        Returns
        -------

        """
        full_path = polish_path(path)
        if _reporter is None:
            _reporter = Reporter()

        file_hash = gen_file_hash(path)
        if add_path_to_sources:
            sources.append(os.path.split(full_path)[0])

        sourceable_cursor = self.add_sourceable(full_path)
        color_hash_cursor = self.add_color_hash(full_path)
        source_cursors = []
        for source in sources:
            source_cursor = self.add_source(file_hash, source)
            source_cursors.append(source_cursor)

        _reporter.update_with(sourceable_cursor, color_hash_cursor, source_cursors)

        return _reporter

    def catalog_directory(self, directory: str, add_paths_to_sources: bool = False):
        directory = polish_path(directory)
        reporter = Reporter()
        walk_size = sum([len(x[2]) for x in os.walk(directory)])

        with tqdm(total=walk_size, desc=f'Cataloging "{directory}"') as prog:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    self.catalog_file(os.path.join(root, file), [], add_paths_to_sources, _reporter=reporter)
                    prog.update(1)

        return reporter

    # Statics
    @classmethod
    def ignore_unique_violation_of(cls, function: functools.partial):
        try:
            return function()
        except sqlite3.IntegrityError as e:  # This will happen if it exists already
            if not str(e).startswith("UNIQUE"):
                raise e

    @classmethod
    def polish_path(cls, path: str) -> str:
        full_path = os.path.abspath(path)
        full_path = os.path.normpath(full_path)
        full_path = full_path.replace("\\", "/")
        return full_path