#!/usr/bin/env python3
# This file is explained in the Checkmk User Guide:
# https://docs.checkmk.com/master/en/devel_special_agents.html#check_plugin
# 
# Store in your Checkmk site at:
# local/lib/python3/cmk_addons/plugins/ometemp/agent_based/ometemp.py

from cmk.agent_based.v2 import AgentSection, CheckPlugin, Service, Result, State, Metric, check_levels
import itertools
import json

def parse_ometemp(string_table):
    flatlist = list(itertools.chain.from_iterable(string_table))
    parsed = json.loads(" ".join(flatlist).replace("'", "\""))
    return parsed

def discover_ometemp(section):
    yield Service()

def check_ometemp(section):
    t = section['current']['temperature_2m']
    if t < 0.0:
        yield Result(state=State.CRIT, summary="Brrrrrr!")
    elif t < 5.0:
        yield Result(state=State.WARN, summary="It's getting cold...")
    else:
        yield Result(state=State.OK, summary="Nice here.")
    return

agent_section_ometemp = AgentSection(
    name = "ometemp",
    parse_function = parse_ometemp,
)

check_plugin_myhostgroups = CheckPlugin(
    name = "ometemp",
    service_name = "Open Meteo temperature (2m)",
    discovery_function = discover_ometemp,
    check_function = check_ometemp,
)
