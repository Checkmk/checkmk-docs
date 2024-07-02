#!/usr/bin/env python3
# This file is NOT yet explained in the Checkmk User Guide, it will be soon:
# https://docs.checkmk.com/master/en/devel_check_plugins.html
# 
# Store in your Checkmk site at:
# local/lib/python3/cmk_addons/plugins/myhostgroups/graphing/myhostgroups.py
#
# Do not to forget to delete the old files using the unversioned API:
# local/share/check_mk/web/plugins/metrics/myhostgroups_advanced_metrics.py etc.

from cmk.graphing.v1 import Title
from cmk.graphing.v1.graphs import Graph, MinimalRange
from cmk.graphing.v1.metrics import Color, DecimalNotation, Metric, Unit
from cmk.graphing.v1.perfometers import Closed, FocusRange, Open, Perfometer

metric_myhostgroups_services_ok_perc = Metric(
    name = "services_ok_perc",
    title = Title("Percentage of services in OK state"),
    unit = Unit(DecimalNotation("%")),
    color = Color.ORANGE,
)

metric_myhostgroups_hosts_up_perc = Metric(
    name = "hosts_up_perc",
    title = Title("Percentage of hosts in UP state"),
    unit = Unit(DecimalNotation("%")),
    color = Color.PURPLE,
)

metric_myhostgroups_services_ok = Metric(
    name = "num_services_ok",
    title = Title("Number of services in OK state"),
    unit = Unit(DecimalNotation("")),
    color = Color.BLUE,
)

metric_myhostgroups_hosts_up = Metric(
    name = "num_hosts_up",
    title = Title("Number of hosts in UP state"),
    unit = Unit(DecimalNotation("")),
    color = Color.YELLOW,
)

metric_myhostgroups_services = Metric(
    name = "num_services",
    title = Title("Number of services in group"),
    unit = Unit(DecimalNotation("")),
    color = Color.PINK,
)

metric_myhostgroups_hosts = Metric(
    name = "num_hosts",
    title = Title("Number of hosts in group"),
    unit = Unit(DecimalNotation("")),
    color = Color.PINK,
)

graph_myhostgroups_combined = Graph(
    name = "services_ok_comparison",
    title = Title("Services in OK state out of total"),
    simple_lines=[ "num_services", "num_services_ok" ],
    minimal_range=MinimalRange(0, 50),
)

perfometer_myhostgroups_advanced = Perfometer(
    name = "myhostgroups_advanced",
    focus_range = FocusRange(Closed(0), Closed(100)),
    segments = [ "services_ok_perc" ],
)
