#!/usr/bin/env python3
# This file is explained in the Checkmk User Guide:
# https://docs.checkmk.com/master/en/devel_check_plugins_snmp.html#simple_snmp_plugin
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
    result = {}
    result["contact"] = string_table[0][0]
    result["name"] = string_table[0][1]
    result["location"] = string_table[0][2]
    return result

def discover_flintstone(section):
    yield Service()

def check_flintstone(section):
    missing = 0
    for e in ["contact", "name", "location"]:
        if section[e] == "":
            missing += 1
            yield Result(state=State.CRIT, summary=f"Missing information: {e}!")
    if missing > 0:
        yield Result(state=State.CRIT, summary=f"Missing fields: {missing}!")
    else:
        yield Result(state=State.OK, summary="All required information is available.")

snmp_section_flintstone_setup = SimpleSNMPSection(
    name = "flintstone_base_config",
    parse_function = parse_flintstone,
    detect = startswith(
        ".1.3.6.1.2.1.1.1.0",
        "Flintstones, Inc. Fred Router",
    ),
    fetch = SNMPTree(
        base = '.1.3.6.1.2.1.1',
        oids = ['4.0', '5.0', '6.0'],
    ),
)

check_plugin_flintstone_setup = CheckPlugin(
    name = "flintstone_setup_check",
    sections = [ "flintstone_base_config" ],
    service_name = "Flintstone setup check",
    discovery_function = discover_flintstone,
    check_function = check_flintstone,
)