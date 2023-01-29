import os

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
def strict_sourcer(tmp_path):
    yield Sourcer(strict_sourcer_settings(), os.path.join(tmp_path, "sources.db"))


@pytest.fixture()
def medium_sourcer():
    yield Sourcer(medium_sourcer_settings())


@pytest.fixture()
def lenient_sourcer():
    yield Sourcer(lenient_sourcer_settings())


class TestSourcer:
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
