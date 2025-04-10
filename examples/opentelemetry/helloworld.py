#!/usr/bin/env python3

from opentelemetry import metrics
from random import randint
import time

meter = metrics.get_meter("helloworld.meter")
gauge = meter.create_gauge(
    name = "hellolevel",
    unit = "%",
    description = "Just a random number between 0 and 100"
)

while True:
    val = randint(0, 100)
    print("Value", val)
    gauge.set(val)
    time.sleep(1)
