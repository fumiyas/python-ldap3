"""
"""

# Created on 2016.12.26
#
# Author: Giovanni Cannata
#
# Copyright 2016, 2017 Giovanni Cannata
#
# This file is part of ldap3.
#
# ldap3 is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ldap3 is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with ldap3 in the COPYING and COPYING.LESSER files.
# If not, see <http://www.gnu.org/licenses/>.
from ...core.exceptions import LDAPInvalidDnError
from ... import SEQUENCE_TYPES, MODIFY_DELETE, BASE, DEREF_NEVER
from ...utils.dn import safe_dn


def ad_remove_members_from_groups(connection,
                                  members_dn,
                                  groups_dn,
                                  fix):
    """
    :param connection: a bound Connection object
    :param members_dn: the list of members to remove from groups
    :param groups_dn: the list of groups where members are to be removed
    :param fix: checks for group existence and existing members
    :return: a boolean where True means that the operation was successful and False means an error has happened
    Removes users-groups relations following the Activwe Directory rules: users are removed from groups' member attribute

    """
    if not isinstance(members_dn, SEQUENCE_TYPES):
        members_dn = [members_dn]

    if not isinstance(groups_dn, SEQUENCE_TYPES):
        groups_dn = [groups_dn]

    if connection.check_names:  # builds new lists with sanitized dn
        safe_members_dn = []
        safe_groups_dn = []
        for member_dn in members_dn:
            safe_members_dn.append(safe_dn(member_dn))
        for group_dn in groups_dn:
            safe_groups_dn.append(safe_dn(group_dn))

        members_dn = safe_members_dn
        groups_dn = safe_groups_dn

    error = False

    for group in groups_dn:
        if fix:  # checks for existance of group and for already assigned members
            result = connection.search(group, '(objectclass=*)', BASE, dereference_aliases=DEREF_NEVER, attributes=['member'])

            if not connection.strategy.sync:
                response, result = connection.get_response(result)
            else:
                response, result = connection.response, connection.result

            if not result['description'] == 'success':
                raise LDAPInvalidDnError(group + ' not found')

            existing_member = response[0]['attributes']['member'] if 'member' in response[0]['attributes'] else []
        else:
            existing_member = members_dn

        changes = dict()
        member_to_remove = [member for member in members_dn if member in existing_member]
        if member_to_remove:
            changes['member'] = (MODIFY_DELETE, member_to_remove)
        if changes:
            result = connection.modify(group, changes)
            if not connection.strategy.sync:
                _, result = connection.get_response(result)
            else:
                result = connection.result
            if result['description'] != 'success':
                error = True
                break

    return not error
