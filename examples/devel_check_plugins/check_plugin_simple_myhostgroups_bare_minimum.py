#!/usr/bin/env python3
# This file is explained in the Checkmk User Guide:
# https://docs.checkmk.com/2.2.0/en/devel_check_plugins.html#scaffold

from .agent_based_api.v1 import check_levels, Metric, register, Result, Service, State

def parse_myhostgroups(string_table):
    parsed = {}
    return parsed

def discover_myhostgroups(section):
    yield Service()

def check_myhostgroups(section):
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
