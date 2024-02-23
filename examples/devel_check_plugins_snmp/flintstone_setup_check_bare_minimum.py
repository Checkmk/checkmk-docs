#!/usr/bin/env python3
# This file is explained in the Checkmk User Guide:
# https://docs.checkmk.com/2.2.0/en/devel_check_plugins_snmp.html#scaffold

from .agent_based_api.v1 import register, Result, Service, startswith, SNMPTree, State

def parse_flintstone(string_table):
    return {}

def discover_flintstone(section):
    yield Service()

def check_flintstone(section):
    yield Result(state=State.OK, summary="Everything is fine")

register.snmp_section(
    name = "flintstone_base_config",
    parse_function = parse_flintstone,
    detect = startswith(".1.3.6.1.2.1.1.1.0", "Flintstone"),
    fetch = SNMPTree(base='.1.3.6.1.2.1.1', oids=['4.0']),
)

register.check_plugin(
    name = "flintstone_setup_check",
    sections = ["flintstone_base_config"],
    service_name = "Flintstone setup check",
    discovery_function = discover_flintstone,
    check_function = check_flintstone,
)
