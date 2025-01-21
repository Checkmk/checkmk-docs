#!/usr/bin/env python3
# This file is explained in the Checkmk User Guide:
# https://docs.checkmk.com/master/en/devel_special_agents.html#call_config
# 
# Store in your Checkmk site at:
# local/lib/python3/cmk_addons/plugins/hellospecial/server_side_calls/special_agent.py

from cmk.server_side_calls.v1 import noop_parser, SpecialAgentConfig, SpecialAgentCommand

def _agent_arguments(params, host_config):
    yield SpecialAgentCommand(command_arguments=[])

special_agent_hellospecial = SpecialAgentConfig(
    name="hellospecial",
    parameter_parser=noop_parser,
    commands_function=_agent_arguments
)
