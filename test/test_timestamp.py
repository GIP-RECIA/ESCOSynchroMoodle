"""
Module pour les tests vis à vis des timestamps
"""

import os
import tempfile

import pytest

from synchromoodle import timestamp
from synchromoodle.config import TimestampStoreConfig


@pytest.fixture(name='tmp_file')
def fixture_tmp_file():
    """Créé un fichier factice temporaire pour stocker les timestamps."""
    filed, tmp_file = tempfile.mkstemp()
    os.close(filed)
    yield tmp_file
    os.remove(tmp_file)


def test_mark(tmp_file):
    """
    Test la création de timestamps.

    :param tmp_file: Le fichier pour stocker les timestamps
    """
    time_stamp = timestamp.TimestampStore(TimestampStoreConfig(file=tmp_file))
    time_stamp.mark("UAI1")
    assert time_stamp.get_timestamp("UAI1") == time_stamp.now
    time_stamp.mark("UAI2")
    assert time_stamp.get_timestamp("UAI2") == time_stamp.now


def test_read_write(tmp_file):
    """
    Test la lecture/écriture de timestamps.

    :param tmp_file: Le fichier pour stocker les timestamps
    """
    time_stamp1 = timestamp.TimestampStore(TimestampStoreConfig(file=tmp_file))
    time_stamp2 = timestamp.TimestampStore(TimestampStoreConfig(file=tmp_file), now=time_stamp1.now)
    time_stamp1.mark("UAI")
    time_stamp1.write()
    time_stamp2.read()
    assert time_stamp2.get_timestamp("UAI") == time_stamp1.now

    time_stamp1.mark("UAI2")
    time_stamp1.write()
    time_stamp2.read()
    assert time_stamp2.get_timestamp("UAI2") == time_stamp1.now
