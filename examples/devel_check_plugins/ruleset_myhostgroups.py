#!/usr/bin/env python3
# This file is NOT yet explained in the Checkmk User Guide, it will be soon:
# https://docs.checkmk.com/master/en/devel_check_plugins.html
# 
# Store in your Checkmk site at:
# local/lib/python3/cmk_addons/plugins/myhostgroups/rulesets/myhostgroups.py
#
# Do not to forget to delete the old file using the unversioned API:
# local/share/check_mk/web/plugins/wato/myhostgroups_advanced_parameters.py

from cmk.rulesets.v1 import Label, Title
from cmk.rulesets.v1.form_specs import (
    BooleanChoice,
    DefaultValue,
    DictElement,
    Dictionary,
    Float,
    LevelDirection,
    SimpleLevels,
)
from cmk.rulesets.v1.rule_specs import CheckParameters, HostAndItemCondition, Topic


def _parameter_form() -> Dictionary:
    return Dictionary(
        elements = {
            "hosts_up_lower": DictElement(
                parameter_form = SimpleLevels(
                    level_direction = LevelDirection.LOWER,
                    form_spec_template = Float(),
                    prefill_fixed_levels = DefaultValue(value=(80.0, 90.0)),
                    title=Title("Lower percentage threshold for host in UP status"),
                ),
                required = True,
            ),
            "services_ok_lower": DictElement(
                    parameter_form = SimpleLevels(
                    level_direction = LevelDirection.LOWER,
                    form_spec_template = Float(),
                    prefill_fixed_levels = DefaultValue(value=(80.0, 90.0)),
                    title = Title("Lower percentage threshold for services in OK status"),
                ),
                required = True,
            ),

        }
    )


rule_spec_myhostgroups = CheckParameters(
    name = "myhostgroups_advanced",
    topic = Topic.GENERAL,
    parameter_form = _parameter_form,
    title = Title("Host group status"),
    condition = HostAndItemCondition(item_title=Title("Host group status")),
)
