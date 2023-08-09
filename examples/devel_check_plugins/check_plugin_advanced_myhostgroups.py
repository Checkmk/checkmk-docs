#!/usr/bin/env python3

# pylint: disable=missing-function-docstring
from .agent_based_api.v1 import register, Result, Service, State


def parse_myhostgroups(string_table):
    # [["check_mk", "myhost1,myhost2,myhost3,myhost4", "4", "3", "87", "56"],
    #  ["foo", "myhost11, myhost22, myhost33,myhost44", "4", "4", "112", "108"]]
    parsed = {}
    for line in string_table:
        column_names = (
            "members",
            "num_hosts",
            "num_hosts_up",
            "num_services",
            "num_services_ok",
        )
        parsed[line[0]] = dict(zip(column_names, line[1:]))
    return parsed


register.agent_section(
    name="myhostgroups",
    parse_function=parse_myhostgroups,
)


def discover_myhostgroups(section):
    yield Service()


def check_myhostgroups(section):
    # {"check_mk": {"members": "myhost1,myhost2,myhost3,myhost4"},
    #  "foo": {"members": "myhost11,myhost22,myhost33,myhost44"}}
    attr = section.get("check_mk")
    hosts = attr["members"] if attr else ""
    if hosts:
        yield Result(state=State.CRIT, summary=f"Default group is not empty: {hosts}")
    else:
        yield Result(state=State.OK, summary="Everything is fine")


register.check_plugin(
    name="myhostgroups",
    service_name="Hostgroup check_mk",
    discovery_function=discover_myhostgroups,
    check_function=check_myhostgroups,
)


def discover_myhostgroups_advanced(section):
    for group in section:
        if group != "check_mk":
            yield Service(item=group)


def check_myhostgroups_advanced(item, section):
    # {"check_mk": {"members": "myhost1,myhost2,myhost3,myhost4", "num_hosts": "4", "num_hosts_up": "3", "num_services": "87", "num_services_ok": "56"},
    #  "foo": {"members": "myhost11,myhost22,myhost33,myhost44", "num_hosts": "4", "num_hosts_up": "4", "num_services": "87", "num_services_ok": "56"}}
    attr = section.get(item)
    if attr:
        yield Result(state=State.OK, summary=f"Hosts in this group: {attr['members']}")
    else:
        yield Result(state=State.CRIT, summary="Group is empty or has been deleted")


register.check_plugin(
    name="myhostgroups_advanced",
    sections=["myhostgroups"],
    service_name="Hostgroup %s",
    discovery_function=discover_myhostgroups_advanced,
    check_function=check_myhostgroups_advanced,
)
