# coding: utf-8
"""
Moduel permettant les opérations nécéssaires à la
mise en place du ldap pour les tests
"""

from io import StringIO
from pkgutil import get_data

from test.utils import ldif
from ldap3 import Connection, LEVEL
from ldap3.core.exceptions import LDAPNoSuchObjectResult
from synchromoodle.ldaputils import Ldap

def _remove_all_in(connection: Connection, dn: str):
    try:
        connection.search(dn, '(objectClass=*)', search_scope=LEVEL)
    except LDAPNoSuchObjectResult:
        return

    for entry in connection.entries:
        connection.delete(entry.entry_dn)


def reset(ldap: Ldap):
    """Remet à jour le ldap passé en paramètre"""
    ldap.connect()
    connection = ldap.connection
    try:
        _remove_all_in(connection, ldap.config.groups_dn)
        _remove_all_in(connection, ldap.config.personnes_dn)
        _remove_all_in(connection, ldap.config.structures_dn)
    finally:
        ldap.disconnect()


class LDIFLoader(ldif.LDIFRecordList):
    """Classe LDIFLoader"""
    def __init__(self, connection: Connection,
                 input_file, ignored_attr_types=None, max_entries=0, process_url_schemes=None):
        super().__init__(input_file, ignored_attr_types, max_entries, process_url_schemes)
        self.connection = connection

    def handle_modify(self, dn, modops, controls=None):
        pass

    def handle(self, dn, entry):
        self.connection.add(dn, attributes=entry)


def run_ldif(path: str, ldap: Ldap):
    """
    Load file from ldif format.

    :param path: path to ldif file
    :param ldap: ldap adapter
    """
    ldif_data = str(get_data('test', path), 'utf8')
    with StringIO(ldif_data) as ldif_file:
        loader = LDIFLoader(ldap.connection, ldif_file)
        loader.parse()
