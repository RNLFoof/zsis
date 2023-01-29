import inspect
import os
import sqlite3

import pytest

from zsis.classes.Sourcer import Sourcer
from zsis.classes.SourcerSettings import SourcerSettings


@pytest.fixture()
def strict_sourcer_settings():
    yield SourcerSettings(10, 10, 8, False)


@pytest.fixture()
def medium_sourcer_settings():
    yield SourcerSettings(7, 7, 5, False)


@pytest.fixture()
def lenient_sourcer_settings():
    yield SourcerSettings(4, 4, 2, False)


@pytest.fixture()
def strict_sourcer(tmp_path, strict_sourcer_settings):
    yield Sourcer(strict_sourcer_settings, os.path.join(tmp_path, "sources.db"))


@pytest.fixture()
def medium_sourcer():
    yield Sourcer(medium_sourcer_settings())


@pytest.fixture()
def lenient_sourcer(tmp_path, lenient_sourcer_settings):
    yield Sourcer(lenient_sourcer_settings, os.path.join(tmp_path, "sources.db"))


class TestSourcer:
    module_path = inspect.getfile(inspect.currentframe())
    module_dir = os.path.split(module_path)[0]
    big_hippo_path = os.path.join(module_dir, r"../images/subfolder/big hippo.png")
    small_hippo_path = os.path.join(module_dir, r"../images/subfolder/small hippo.png")
    big_white_path = os.path.join(module_dir, r"../images/big white.jpg")
    small_white_path = os.path.join(module_dir, r"../images/small white.png")

    def test_gen_image_hash(self, strict_sourcer, lenient_sourcer):
        with strict_sourcer:
            strict_big_hippo = strict_sourcer.gen_color_hash(self.big_hippo_path)
            strict_small_hippo = strict_sourcer.gen_color_hash(self.small_hippo_path)
            strict_big_white = strict_sourcer.gen_color_hash(self.big_white_path)
            strict_small_white = strict_sourcer.gen_color_hash(self.small_white_path)

        assert strict_big_hippo == "25d5700e229b26e8d7fb5b9c739ed655"
        assert strict_small_hippo == "16f3a85d2aa5052ce9f04acf064a1db7"
        assert strict_big_white == strict_small_white

        with lenient_sourcer:
            lenient_big_hippo = lenient_sourcer.gen_color_hash(self.big_hippo_path)
            lenient_small_hippo = lenient_sourcer.gen_color_hash(self.small_hippo_path)
            lenient_big_white = lenient_sourcer.gen_color_hash(self.big_white_path)
            lenient_small_white = lenient_sourcer.gen_color_hash(self.small_white_path)

        assert lenient_big_hippo == lenient_small_hippo
        assert lenient_big_white == lenient_small_white
        assert lenient_big_hippo != lenient_big_white

    def test_gen_file_hash(self):
        assert Sourcer.gen_file_hash(self.big_hippo_path) \
               == b'W\xed\xa4\xe5h\xa5\xe4\xe6q\x1e\x9f#\x9do>f\x8d\xaf\xe1u<\xb1\x04x\x17\xea\x8f\xfbu\x1d\x02x'

    def test_ignore_unique_violation_of(self):
        def raise_exception():
            raise Exception()

        def raise_integrity_error():
            raise sqlite3.IntegrityError()

        def raise_unique_integrity_error():
            raise sqlite3.IntegrityError("UNIQUE")

        with pytest.raises(Exception):
            Sourcer.ignore_unique_violation_of(raise_exception)
        with pytest.raises(sqlite3.IntegrityError):
            Sourcer.ignore_unique_violation_of(raise_integrity_error)
        Sourcer.ignore_unique_violation_of(raise_unique_integrity_error)

    def test_abs_path_if_local(self):
        google_path = r"https://www.google.com/"
        assert Sourcer.abs_path_if_local(google_path) == google_path

        working_directory = os.path.abspath("")
        assert Sourcer.abs_path_if_local(os.path.abspath("")) == working_directory

    def test_polish_path(self):
        assert Sourcer.polish_path(r"https://www.google.com/") == "https:/www.google.com"
        assert Sourcer.polish_path(r"https:\\www.google.com/") == "https:/www.google.com"

        working_directory = os.path.abspath("").replace("\\", "/")
        assert Sourcer.polish_path(working_directory) == working_directory
