#!/usr/bin/env python3
# This file is explained in the Checkmk User Guide:
# https://docs.checkmk.com/master/en/devel_check_plugins.html#rule_set
# 
# Store in your Checkmk site at:
# ~/local/lib/python3/cmk_addons/plugins/myhostgroups/rulesets/ruleset_myhostgroups.py
#
# If you have implemented the example presented in Checkmk 2.2.0 for the unversioned API:
# 1. Delete the "Host group status" rule in the GUI.
# 2. Delete the ~/local/share/check_mk/web/plugins/wato/myhostgroups_advanced_parameters.py file.

from cmk.rulesets.v1 import Label, Title
from cmk.rulesets.v1.form_specs import BooleanChoice, DefaultValue, DictElement, Dictionary, Float, LevelDirection, SimpleLevels
from cmk.rulesets.v1.rule_specs import CheckParameters, HostAndItemCondition, Topic

def _parameter_form() -> Dictionary:
    return Dictionary(
        elements = {
            "hosts_up_lower": DictElement(
                parameter_form = SimpleLevels(
                    title = Title("Lower percentage threshold for host in UP status"),
                    form_spec_template = Float(),
                    level_direction = LevelDirection.LOWER,
                    prefill_fixed_levels = DefaultValue(value=(90.0, 80.0)),
                ),
                required = True,
            ),
            "services_ok_lower": DictElement(
                parameter_form = SimpleLevels(
                    title = Title("Lower percentage threshold for services in OK status"),
                    form_spec_template = Float(),
                    level_direction = LevelDirection.LOWER,
                    prefill_fixed_levels = DefaultValue(value=(90.0, 80.0)),
                ),
                required = True,
            ),
        }
    )

rule_spec_myhostgroups = CheckParameters(
    name = "myhostgroups_advanced",
    title = Title("Host group status"),
    topic = Topic.GENERAL,
    parameter_form = _parameter_form,
    condition = HostAndItemCondition(item_title=Title("Host group name")),
)
