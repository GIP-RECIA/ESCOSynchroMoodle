# coding: utf-8

import re
from pkgutil import get_data

import sqlparse
from cachetools import cached, Cache

from synchromoodle.dbutils import Database

__statements_cache = Cache(maxsize=100)


def init(db: Database):
    run_script('data/ddl.sql', db)


def reset(db: Database):
    run_script('data/ddl.sql', db)


@cached(__statements_cache)
def _get_statements(path: str):
    script_data = str(get_data('test', path), 'utf8')
    cleaned_script_data = re.sub('/\*.+?\*/;\n', "", script_data, flags=re.MULTILINE)
    statements = sqlparse.split(cleaned_script_data)
    return statements


def run_script(script: str, db: Database, connect=True):
    if connect:
        db.connect()
    try:
        statements = _get_statements(script)
        for statement in statements:
            db.mark.execute(statement)
            while db.mark.nextset():
                pass
        db.connection.commit()
    finally:
        if connect:
            db.disconnect()
