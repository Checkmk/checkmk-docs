#!/usr/bin/env python3
# This file is explained in the Checkmk User Guide:
# https://docs.checkmk.com/master/en/devel_special_agents.html#rule_config
# 
# Store in your Checkmk site at:
# local/lib/python3/cmk_addons/plugins/hellospecial/rulesets/special_agent.py

from cmk.rulesets.v1.form_specs import Dictionary
from cmk.rulesets.v1.rule_specs import SpecialAgent, Topic, Help, Title

def _formspec():
    return Dictionary(
        title=Title("Hello special!"),
        help_text=Help("This rule is to demonstrate the minimum special agent."),
        elements={}
    )

rule_spec_hellospecial = SpecialAgent(
    topic=Topic.GENERAL,
    name="hellospecial",
    title=Title("Hello special!"),
    parameter_form=_formspec
)
