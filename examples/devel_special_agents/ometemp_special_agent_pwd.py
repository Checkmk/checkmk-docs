#!/usr/bin/env python3
# This file is explained in the Checkmk User Guide:
# https://docs.checkmk.com/master/en/devel_special_agents.html#use_pwd
# 
# Store in your Checkmk site at:
# local/lib/python3/cmk_addons/plugins/ometemp/rulesets/special_agent.py

from cmk.rulesets.v1.form_specs import Dictionary, DictElement, Float, String, Password, migrate_to_password
from cmk.rulesets.v1.rule_specs import SpecialAgent, Topic, Help, Title

def _formspec():
    return Dictionary(
        title=Title("Open-Meteo temperature"),
        help_text=Help("This rule is used to showcase a special agent with configuration."),
        elements={
            "latitude": DictElement(
                required=True,
                parameter_form=Float(
                    title=Title("Latitude in degrees (decimal notation)"),
                ),
            ),
            "longitude": DictElement(
                required=True,
                parameter_form=Float(
                    title=Title("Longitude in degrees (decimal notation)"),
                ),
            ),
            "user": DictElement(
                required=True,
                parameter_form=String(
                    title=Title("User ID for login"),
                    prefill=DefaultValue("monitoring"),
                ),
            ),
            "password": DictElement(
                required=True,
                parameter_form=Password(
                    title=Title("Password for this user"),
                    migrate=migrate_to_password,
                ),
            ),
        }
    )

rule_spec_hellospecial = SpecialAgent(
    topic=Topic.ENVIRONMENTAL,
    name="ometemp",
    title=Title("Open-Meteo temperature"),
    parameter_form=_formspec
)
