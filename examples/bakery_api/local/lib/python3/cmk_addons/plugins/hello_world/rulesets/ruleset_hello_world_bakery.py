#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Shebang only needed for editor!

# Copyright (C) 2021-2022 Mattias Schlenker <ms@mattiasschlenker.de> for tribe29 GmbH
# Copyright (C) 2022-2025 Mattias Schlenker <mattias.schlenker@checkmk.com> for Checkmk GmbH
# License: GNU General Public License v2
#
# Reference for details:
# https://docs.checkmk.com/latest/en/devel_check_plugins.html
# https://docs.checkmk.com/latest/en/bakery_api.html
#
# This is the Setup GUI for agent plugin distribution of our "Hello world!" plugin. It
# defines the parameters that can be configured using the GUI and that will eventually
# be written to the configuration on the host running the agent.
#
# Note: Only commercial editions include the agent bakery, Checkmk Raw ignores this file.

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

# Create a function that returns a tuple containing default thresholds,
# the title may be an arbitary string, this serves three tasks:
# 1. Define reasonable defaults
# 2. Provide an entry field with proper range and label for the setup
# 3. Create a dictionary passed to the agent based plugin, either using
#    defaults or the overriden values 

def _parameter_form_bakery():
    return Dictionary(
        elements = {
            "user": DictElement(
                parameter_form = String(
                    title = Title("User for example plugin"),
                )
            ),
            "content": DictElement(
                parameter_form = String(
                    title = Title("The actual content"),
                )
            ),
            "interval": DictElement(
                parameter_form = TimeSpan(
                    title = Title("Run asynchronously"),
                    label = Label("Interval for collecting data"),
                    displayed_magnitudes = [TimeMagnitude.SECOND, TimeMagnitude.MINUTE],
                    prefill = DefaultValue(300.0),
                )
            )
        }
    )
               
# Create a rulespec to be used in your agent based plugin:
#
# CheckParameterRulespecWithoutItem - skip the item: 
# check_helloworld(params, section):
# If more than one value is to be checked, you probably would use the item

rule_spec_hello_world_bakery = AgentConfig(
    name = "hello_world",
    title = Title("Hello bakery!"),
    topic = Topic.GENERAL,
    parameter_form = _parameter_form_bakery,
)

