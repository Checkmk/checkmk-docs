#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Shebang only needed for editor!

from cmk.rulesets.v1 import Label, Title, Help
from cmk.rulesets.v1.form_specs import (
    BooleanChoice,
    DefaultValue,
    DictElement,
    Dictionary,
    String,
    TimeSpan,
    TimeMagnitude
)
from cmk.rulesets.v1.rule_specs import AgentConfig, HostCondition, Topic 

def _parameter_form_bakery():
    return Dictionary(
        elements = {}
    )
               
rule_spec_hello_world_bakery = AgentConfig(
    name = "hello_world",
    title = Title("Hello bakery!"),
    topic = Topic.GENERAL,
    parameter_form = _parameter_form_bakery,
)

