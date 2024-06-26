#!/usr/bin/env python3
# This file is explained in the Checkmk User Guide:
# https://docs.checkmk.com/master/en/devel_check_plugins.html#scaffold

from cmk.agent_based.v2 import AgentSection, CheckPlugin, Service, Result, State, Metric, check_levels

def parse_myhostgroups(string_table):
    parsed = {}
    return parsed

def discover_myhostgroups(section):
    yield Service()

def check_myhostgroups(section):
    yield Result(state=State.OK, summary="Everything is fine")

agent_section_myhostgroups = AgentSection(
    name = "myhostgroups",
    parse_function = parse_myhostgroups,
)

check_plugin_myhostgroups = CheckPlugin(
    name = "myhostgroups",
    service_name = "Host group check_mk",
    discovery_function = discover_myhostgroups,
    check_function = check_myhostgroups,
)
