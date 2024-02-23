#!/usr/bin/env python3
# This file is explained in the Checkmk User Guide:
# https://docs.checkmk.com/2.2.0/en/devel_check_plugins.html#extend

from .agent_based_api.v1 import check_levels, Metric, register, Result, Service, State

def parse_myhostgroups(string_table):
    # string_table = [
    #     ['check_mk, 'myhost1,myhost2,myhost3,myhost4', '4', '3', '87', '56'],
    #     ['foo', 'myhost11,myhost22,myhost33,myhost44', '4', '4', '112', '108']
    # ]
    parsed = {}
    column_names = [
        "name",
        "members",
        "num_hosts",
        "num_hosts_up",
        "num_services",
        "num_services_ok",
    ]
    for line in string_table:
        parsed[line[0]] = {}
        for n in range(1, len(column_names)):
            parsed[line[0]][column_names[n]] = line[n]
    # parsed = {
    #     'check_mk': {
    #         'members': 'myhost1,myhost2,myhost3,myhost4', 
    #         'num_hosts': '4',
    #         'num_hosts_up': '3',
    #         'num_services': '87',
    #         'num_services_ok': '56'
    #     },
    #     'foo': {
    #         'members': 'myhost11,myhost22,myhost33,myhost44',
    #         'num_hosts': '4',
    #         'num_hosts_up': '4',
    #         'num_services': '112',
    #         'num_services_ok': '108'
    #     }
    # }
    return parsed


def discover_myhostgroups(section):
    yield Service()

def check_myhostgroups(section):
    attr = section.get("check_mk")
    hosts = attr["members"] if attr else ""
    if hosts:
        yield Result(state=State.CRIT, summary=f"Default group is not empty; Current member list: {hosts}")
    else:
        yield Result(state=State.OK, summary="Everything is fine")


def discover_myhostgroups_advanced(section):
    for group in section:
        if group != "check_mk":
            yield Service(item=group)

def check_myhostgroups_advanced(item, section):
    attr = section.get(item)
    if not attr:
        yield Result(state=State.CRIT, summary="Group is empty or has been deleted")
        return

    yield Result(state=State.OK, summary=f"{attr['num_hosts']} hosts in this group: {attr['members']}")


register.agent_section(
    name = "myhostgroups",
    parse_function = parse_myhostgroups,
)

register.check_plugin(
    name = "myhostgroups",
    service_name = "Host group check_mk",
    discovery_function = discover_myhostgroups,
    check_function = check_myhostgroups,
)

register.check_plugin(
    name = "myhostgroups_advanced",
    sections = ["myhostgroups"],
    service_name = "Host group %s",
    discovery_function = discover_myhostgroups_advanced,
    check_function = check_myhostgroups_advanced,
)
