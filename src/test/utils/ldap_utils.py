# coding: utf-8
from io import StringIO
from pkgutil import get_data

import ldap
import ldif
from ldap import modlist
from ldap.ldapobject import SimpleLDAPObject

from synchromoodle.ldaputils import Ldap


def _remove_all_in(connection: SimpleLDAPObject, dn: str):
    result = connection.search_ext_s(dn, ldap.SCOPE_ONELEVEL, None, [])
    for item in result:
        dn, data = item
        connection.delete_s(dn)


def reset(l: Ldap):
    l.connect()
    connection = l.connection
    try:
        _remove_all_in(connection, l.config.groupsDN)
        _remove_all_in(connection, l.config.personnesDN)
        _remove_all_in(connection, l.config.structuresDN)
    finally:
        l.disconnect()


def run_ldif(path: str, l: Ldap):
    ldif_data = str(get_data('test', path), 'utf8')
    with StringIO(ldif_data) as ldif_file:
        recordlist = ldif.LDIFRecordList(ldif_file)
        recordlist.parse()
    for record in recordlist.all_records:
        dn = record[0]
        data = record[1]
        changetype = data.pop('changetype', 'add')
        change_method = getattr(l.connection, changetype + '_s')
        if changetype == 'add':
            l.connection.add_s(dn, modlist.addModlist(data))
        elif changetype == 'modify':
            raise Exception("modify changetype is not supported.")
        elif changetype == 'delete':
            l.connection.delete_s(dn)
        elif changetype == 'modrdn':
            l.connection.modrdn(dn, data.get('newrdn'), data.get('deleteoldrdn', 1))
        else:
            raise Exception("Invalid changetype: " + changetype)


def add_personne(l: Ldap, rdn: str, entry: dict):
    l.connection.add_s(rdn + ',' + l.config.personnesDN, modlist.addModlist(entry))


def add_group(l: Ldap, rdn: str, entry: dict):
    l.connection.add_s(rdn + ',' + l.config.groupsDN, modlist.addModlist(entry))


def add_structure(l: Ldap, rdn: str, entry: dict):
    l.connection.add_s(rdn + ',' + l.config.structuresDN, modlist.addModlist(entry))
