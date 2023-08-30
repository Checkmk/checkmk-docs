from cmk.gui.i18n import _

from cmk.gui.valuespec import (
    Dictionary,
    Integer,
    TextInput,
    Tuple,
)

from cmk.gui.plugins.wato.utils import (
    CheckParameterRulespecWithItem,
    rulespec_registry,
    RulespecGroupCheckParametersApplications,
)


def _item_valuespec_myhostgroups_advanced():
    return TextInput(title="Host group name", help="You can restrict this rule to certain services of the specified hosts.")


def _parameter_valuespec_myhostgroups_advanced():
    return Dictionary(
        elements=[
            ("hosts_up_lower", Tuple(
                title=_("Lower percentage threshold for host in UP status"),
                elements=[Integer(title=_("Warning")), Integer(title=_("Critical"))],
                )
            ),
            ("services_ok_lower", Tuple(
                title=_("Lower percentage threshold for services in OK status"),
                elements=[Integer(title=_("Warning")), Integer(title=_("Critical"))],
                )
            ),
        ],
    )


rulespec_registry.register(
    CheckParameterRulespecWithItem(
        check_group_name="myhostgroups_advanced",
        group=RulespecGroupCheckParametersApplications,
        match_type="dict",
        item_spec=_item_valuespec_myhostgroups_advanced,
        parameter_valuespec=_parameter_valuespec_myhostgroups_advanced,
        title=lambda: _("Host group status"),
    )
)
