#!/usr/bin/env python3
# This file is explained in the Checkmk User Guide:
# https://docs.checkmk.com/2.2.0/en/devel_check_plugins.html#use_ruleset

from .agent_based_api.v1 import check_levels, Metric, register, Result, Service, State

def parse_myhostgroups(string_table):
    # string_table = [
    #     ['check_mk, 'myhost1,myhost2,myhost3,myhost4', '4', '3', '87', '56'],
    #     ['foo', 'myhost11,myhost22,myhost33,myhost44', '4', '4', '112', '108']
    # ]
    parsed = {}
    column_names = [
        "name",
        "members",
        "num_hosts",
        "num_hosts_up",
        "num_services",
        "num_services_ok",
    ]
    for line in string_table:
        parsed[line[0]] = {}
        for n in range(1, len(column_names)):
            parsed[line[0]][column_names[n]] = line[n]
    # parsed = {
    #     'check_mk': {
    #         'members': 'myhost1,myhost2,myhost3,myhost4', 
    #         'num_hosts': '4',
    #         'num_hosts_up': '3',
    #         'num_services': '87',
    #         'num_services_ok': '56'
    #     },
    #     'foo': {
    #         'members': 'myhost11,myhost22,myhost33,myhost44',
    #         'num_hosts': '4',
    #         'num_hosts_up': '4',
    #         'num_services': '112',
    #         'num_services_ok': '108'
    #     }
    # }
    return parsed


def discover_myhostgroups(section):
    yield Service()

def check_myhostgroups(section):
    attr = section.get("check_mk")
    hosts = attr["members"] if attr else ""
    if hosts:
        yield Result(state=State.CRIT, summary=f"Default group is not empty; Current member list: {hosts}")
    else:
        yield Result(state=State.OK, summary="Everything is fine")


def discover_myhostgroups_advanced(section):
    for group in section:
        if group != "check_mk":
            yield Service(item=group)

def check_myhostgroups_advanced(item, params, section):
    hosts_up_lower = params["hosts_up_lower"]
    services_ok_lower = params["services_ok_lower"]
    attr = section.get(item)
    if not attr:
        yield Result(state=State.CRIT, summary="Group is empty or has been deleted")
        return

    members = attr["members"]
    num_hosts = int(attr["num_hosts"])
    num_hosts_up = int(attr["num_hosts_up"])
    num_services = int(attr["num_services"])
    num_services_ok = int(attr["num_services_ok"])

    yield Result(
        state=State.OK,
        summary=f"{num_hosts} hosts in this group",
        details=f"{num_hosts} hosts in this group: {members}"
    )
    
    hosts_up_perc = 100.0 * num_hosts_up / num_hosts
    yield from check_levels(
        hosts_up_perc,
        levels_lower = (hosts_up_lower),
        metric_name = "hosts_up_perc",
        label = "UP hosts",
        boundaries = (0.0, 100.0),
        notice_only = True,
    )
    services_ok_perc = 100.0 * num_services_ok / num_services
    yield from check_levels(
        services_ok_perc,
        levels_lower = (services_ok_lower),
        metric_name = "services_ok_perc",
        label = "OK services",
        boundaries = (0.0, 100.0),
        notice_only = True,
    )

    yield Metric(name="num_hosts", value=num_hosts)
    yield Metric(name="num_hosts_up", value=num_hosts_up)
    yield Metric(name="num_services", value=num_services)
    yield Metric(name="num_services_ok", value=num_services_ok)


register.agent_section(
    name = "myhostgroups",
    parse_function = parse_myhostgroups,
)

register.check_plugin(
    name = "myhostgroups",
    service_name = "Host group check_mk",
    discovery_function = discover_myhostgroups,
    check_function = check_myhostgroups,
)

register.check_plugin(
    name = "myhostgroups_advanced",
    sections = ["myhostgroups"],
    service_name = "Host group %s",
    discovery_function = discover_myhostgroups_advanced,
    check_function = check_myhostgroups_advanced,
    check_default_parameters = {"hosts_up_lower": (90, 80), "services_ok_lower": (90, 80)},
    check_ruleset_name = "myhostgroups_advanced",
)
