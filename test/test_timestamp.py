import os
import tempfile

import pytest

from synchromoodle import timestamp
from synchromoodle.config import TimestampStoreConfig


@pytest.fixture(name='tmp_file')
def tmp_file():
    fd, tmp_file = tempfile.mkstemp()
    os.close(fd)
    yield tmp_file
    os.remove(tmp_file)


def test_mark(tmp_file):
    ts = timestamp.TimestampStore(TimestampStoreConfig(file=tmp_file))
    ts.mark("UAI1")
    assert ts.get_timestamp("UAI1") == ts.now
    ts.mark("UAI2")
    assert ts.get_timestamp("UAI2") == ts.now


def test_read_write(tmp_file):
    ts1 = timestamp.TimestampStore(TimestampStoreConfig(file=tmp_file))
    ts2 = timestamp.TimestampStore(TimestampStoreConfig(file=tmp_file), now=ts1.now)
    ts1.mark("UAI")
    ts1.write()
    ts2.read()
    assert ts2.get_timestamp("UAI") == ts1.now

    ts1.mark("UAI2")
    ts1.write()
    ts2.read()
    assert ts2.get_timestamp("UAI2") == ts1.now
