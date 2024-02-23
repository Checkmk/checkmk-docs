#!/usr/bin/env python3
# This file is explained in the Checkmk User Guide:
# https://docs.checkmk.com/2.2.0/en/devel_check_plugins.html#write_check_plugin

from .agent_based_api.v1 import check_levels, Metric, register, Result, Service, State

def parse_myhostgroups(string_table):
    # print(string_table)
    # string_table = [
    #     ['check_mk, 'myhost1,myhost2,myhost3,myhost4'],
    #     ['foo', 'myhost11,myhost22,myhost33,myhost44']
    # ]
    parsed = {}
    for line in string_table:
        parsed[line[0]] = {"members": line[1]}
    # print(parsed)
    # parsed = {
    #     'check_mk': {'members': 'myhost1,myhost2,myhost3,myhost4'},
    #     'foo': {'members': 'myhost11,myhost22,myhost33,myhost44'}
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
