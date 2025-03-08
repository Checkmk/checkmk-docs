#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2021 Mattias Schlenker <ms@mattiasschlenker.de> for tribe29 GmbH
# License: GNU General Public License v2
#
# Reference for details:
# https://docs.checkmk.com/latest/en/devel_check_plugins.html
#
# Configuration for a simple perf-o-meter that displays percentage

from cmk.graphing.v1 import Title
from cmk.graphing.v1.graphs import Graph, MinimalRange
from cmk.graphing.v1.metrics import Color, DecimalNotation, Metric, Unit
from cmk.graphing.v1.perfometers import Closed, FocusRange, Open, Perfometer

# Just create the most simple perf-o-meter displaying only one linear value.
# We use the variable "hellolevel" as reference. Since output ranges from 0
# to 100 we just use the full range.

#perfometer_info.append({
#    "type": "linear",
#    "segments": ["hellolevel"],
#    "total": 100.0,
#})

metric_hellolevel = Metric(
    name = "hellolevel",
    title = Title("Hello world level"),
    unit = Unit(DecimalNotation("%")),
    color = Color.PINK,
)

perfometer_hello_world = Perfometer(
    name = "hello_world",
    focus_range = FocusRange(Closed(0), Closed(100)),
    segments = [ "hellolevel" ],
)

