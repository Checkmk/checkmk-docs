#!/usr/bin/env python3
# This file is explained in the Checkmk User Guide:
# https://docs.checkmk.com/master/en/devel_check_plugins_snmp.html#scaffold
#
# Store in your Checkmk site at:
# ~/local/lib/python3/cmk_addons/plugins/flintstone/agent_based/flintstone_setup_check.py

from cmk.agent_based.v2 import (
    CheckPlugin,
    CheckResult,
    startswith,
    DiscoveryResult,
    Result,
    Service,
    SimpleSNMPSection,
    SNMPTree,
    State,
    StringTable,
)

def parse_flintstone(string_table):
    return {}

def discover_flintstone(section):
    yield Service()

def check_flintstone(section):
    yield Result(state=State.OK, summary="Everything is fine")

snmp_section_flintstone_setup = SimpleSNMPSection(
    name = "flintstone_base_config",
    parse_function = parse_flintstone,
    detect = startswith(".1.3.6.1.2.1.1.1.0", "Flintstone"),
    fetch = SNMPTree(base='.1.3.6.1.2.1.1', oids=['4.0']),
)

check_plugin__flintstone_setup = CheckPlugin(
    name = "flintstone_setup_check",
    sections = [ "flintstone_base_config" ],
    service_name = "Flintstone setup check",
    discovery_function = discover_flintstone,
    check_function = check_flintstone,
)