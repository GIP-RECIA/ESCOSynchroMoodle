import os
import tempfile
from datetime import datetime

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
    now = datetime.now()
    ts = timestamp.TimestampStore(TimestampStoreConfig(file=tmp_file))
    ts.mark("UAI1")
    assert ts.get_timestamp("UAI1") == now
    ts.mark("UAI2")
    assert ts.get_timestamp("UAI2") == now


def test_read_write(tmp_file):
    now = datetime.now()
    ts1 = timestamp.TimestampStore(TimestampStoreConfig(file=tmp_file))
    ts2 = timestamp.TimestampStore(TimestampStoreConfig(file=tmp_file))
    ts1.mark("UAI")
    ts1.write()
    ts2.read()
    assert ts2.get_timestamp("UAI") == now
