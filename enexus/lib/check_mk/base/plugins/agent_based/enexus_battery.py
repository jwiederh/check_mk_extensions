#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-

# (c) 2022 Heinlein Support GmbH
#          Robert Sander <r.sander@heinlein-support.de>

# This is free software;  you can redistribute it and/or modify it
# under the  terms of the  GNU General Public License  as published by
# the Free Software Foundation in version 2.  check_mk is  distributed
# in the hope that it will be useful, but WITHOUT ANY WARRANTY;  with-
# out even the implied warranty of  MERCHANTABILITY  or  FITNESS FOR A
# PARTICULAR PURPOSE. See the  GNU General Public License for more de-
# tails. You should have  received  a copy of the  GNU  General Public
# License along with GNU Make; see the file  COPYING.  If  not,  write
# to the Free Software Foundation, Inc., 51 Franklin St,  Fifth Floor,
# Boston, MA 02110-1301 USA.

from typing import NamedTuple, Dict, List

from .agent_based_api.v1 import (
    check_levels,
    contains,
    register,
    Metric,
    OIDEnd,
    Result,
    Service,
    SNMPTree,
    State,
)
from .agent_based_api.v1.type_defs import (
    CheckResult,
    DiscoveryResult,
)

from .utils.temperature import (
    check_temperature,
)

class BatteryStatus(NamedTuple):
    Overall: str
    Fuses: str
    Voltage: str
    Currents: str
    Temperatures: str
    TimeLeft: str
    Quality: str

_status_map = {
    "0": ("error", State.CRIT),
    "1": ("normal", State.OK),
    "2": ("minorAlarm", State.WARN),
    "3": ("majorAlarm", State.CRIT),
    "4": ("disabled", State.OK),
    "5": ("disconnected", State.CRIT),
    "6": ("notPresent", State.UNKNOWN),
    "7": ("minorAndMajor", State.CRIT),
    "8": ("majorLow", State.CRIT),
    "9": ("minorLow", State.WARN),
    "10": ("majorHigh", State.CRIT),
    "11": ("minorHigh", State.WARN),
    "12": ("event", State.WARN),
    "13": ("valueVolt", State.OK),
    "14": ("valueAmp", State.OK),
    "15": ("valueTemp", State.OK),
    "16": ("valueUnit", State.OK),
    "17": ("valuePerCent", State.OK),
    "18": ("critical", State.CRIT),
    "19": ("warning", State.WARN),
}

def parse_enexus_battery(string_table) -> Dict:
    parsed = {}
    if len(string_table) == 4:
        if len(string_table[0]) == 1:
            if len(string_table[0][0]) == 7:
                parsed['Total'] = BatteryStatus(*string_table[0][0])
        for line in string_table[1]:
            parsed['Bank %s' % line[0]] = {'Status': line[1], 'Temperature': {}, 'Current': {}}
        for line in string_table[2]:
            bank, item = line[0].split('.')
            parsed['Bank %s' % bank]['Temperature'][item] = line
        for line in string_table[3]:
            bank, item = line[0].split('.')
            parsed['Bank %s' % bank]['Current'][item] = line
    return parsed

register.snmp_section(
    name="enexus_battery",
    parse_function=parse_enexus_battery,
    fetch=[
        SNMPTree(
            base=".1.3.6.1.4.1.12148.10.10",
            oids=[
                "1.0", # SP2-MIB::batteryStatus
                "4.0", # SP2-MIB::batteryFusesStatus
                "5.1.0", # SP2-MIB::batteryVoltageStatus
                "6.1.0", # SP2-MIB::batteryCurrentsStatus
                "7.1.0", # SP2-MIB::batteryTemperaturesStatus
                "8.1.0", # SP2-MIB::batteryTimeLeftStatus
                "12.1.0", # SP2-MIB::batteryQualityStatus
            ],
        ),
        SNMPTree(
            base=".1.3.6.1.4.1.12148.10.10.18.2.1",
            oids=[
                OIDEnd(),
                "2", # SP2-MIB::batteryBankStatus
            ],
        ),
        SNMPTree(
            base=".1.3.6.1.4.1.12148.10.10.18.3.1",
            oids=[
                OIDEnd(),
                "2", # SP2-MIB::batteryTemperatureStatus
                "3", # SP2-MIB::batteryTemperatureDescription
                "5", # SP2-MIB::batteryTemperatureAlarmEnable
                "6", # SP2-MIB::batteryTemperatureValue
                "7", # SP2-MIB::batteryTemperatureMajorHighLevel
                "8", # SP2-MIB::batteryTemperatureMinorHighLevel
                "9", # SP2-MIB::batteryTemperatureMinorLowLevel
                "10", # SP2-MIB::batteryTemperatureMajorLowLevel
            ],
        ),
        SNMPTree(
            base=".1.3.6.1.4.1.12148.10.10.18.4.1",
            oids=[
                OIDEnd(),
                "2", # SP2-MIB::batteryCurrentStatus
                "3", # SP2-MIB::batteryCurrentDescription
                "5", # SP2-MIB::batteryCurrentAlarmEnable
                "6", # SP2-MIB::batteryCurrentValue
                "7", # SP2-MIB::batteryCurrentMajorHighLevel
                "8", # SP2-MIB::batteryCurrentMinorHighLevel
                "9", # SP2-MIB::batteryCurrentMinorLowLevel
                "10", # SP2-MIB::batteryCurrentMajorLowLevel
            ],
        ),
    ],
    detect=contains(".1.3.6.1.2.1.1.2.0", ".1.3.6.1.4.1.12148.10"),
)

def discover_enexus_battery(section: Dict) -> DiscoveryResult:
    for ind in section.keys():
        yield Service(item=ind)

def check_enexus_battery(item, section: Dict) -> CheckResult:
    battery = section.get(item)
    if battery:
        if item == 'Total':
            for field in section[item]._fields:
                value = getattr(section[item], field)
                text, state = _status_map.get(value, ("unknown", State.UNKNOWN))
                yield Result(state=state, summary="%s: %s" % (field, text))
        else:
            value = section[item]['Status']
            text, state = _status_map.get(value, ("unknown", State.UNKNOWN))
            yield Result(state=state, summary="Status: %s" % text)

register.check_plugin(
    name="enexus_battery",
    sections=["enexus_battery"],
    service_name="eNexus Battery %s",
    discovery_function=discover_enexus_battery,
    check_function=check_enexus_battery,
)

def discover_enexus_battery_temp(section_enexus_battery, section_enexus_status) -> DiscoveryResult:
    for bank in section_enexus_battery.keys():
        if bank != 'Total':
            for temp in section_enexus_battery[bank]['Temperature'].keys():
                if section_enexus_battery[bank]['Temperature'][temp][1] != "4":
                    yield Service(item="%s Temperature %s" % (bank, temp))

def check_enexus_battery_temp(item, params, section_enexus_battery, section_enexus_status) -> CheckResult:
    a, bank, b, t = item.split(" ")
    battery = section_enexus_battery.get('Bank %s' % bank)
    unit = "c"
    if section_enexus_status.temp == "1":
        unit = "f"
    if battery:
        temp = battery['Temperature'].get(t)
        if temp:
            text, state = _status_map.get(temp[1], ("unknown", State.UNKNOWN))
            yield Result(state=state,
                         summary="%s, Status: %s" % (temp[2], text))
            yield from check_temperature(
                reading=float(temp[4]),
                params=params,
                dev_unit=unit,
                dev_levels=(float(temp[6]), float(temp[5])),
                dev_levels_lower=(float(temp[7]), float(temp[8])),
            )

register.check_plugin(
    name="enexus_battery_temp",
    sections=["enexus_battery", 'enexus_status'],
    service_name="eNexus Battery %s",
    discovery_function=discover_enexus_battery_temp,
    check_function=check_enexus_battery_temp,
    check_ruleset_name='temperature',
    check_default_parameters={},
)

def discover_enexus_battery_current(section_enexus_battery, section_enexus_status) -> DiscoveryResult:
    for bank in section_enexus_battery.keys():
        if bank != 'Total':
            for current in section_enexus_battery[bank]['Current'].keys():
                if section_enexus_battery[bank]['Current'][current][1] != "4":
                    yield Service(item="%s Current %s" % (bank, current))

def check_enexus_battery_current(item, section_enexus_battery, section_enexus_status) -> CheckResult:
    a, bank, b, c = item.split(" ")
    battery = section_enexus_battery.get('Bank %s' % bank)
    factor = 1.0
    if section_enexus_status.decimal == "1":
        factor = 10.0
    if battery:
        current = battery['Current'].get(c)
        if current:
            text, state = _status_map.get(current[1], ("unknown", State.UNKNOWN))
            yield Result(state=state,
                         summary="%s, Status: %s" % (current[2], text))
            yield from check_levels(
                value=float(current[4]) / factor,
                levels_upper=(float(current[6]) / factor, float(current[5]) / factor),
                levels_lower=(float(current[7]) / factor, float(current[8]) / factor),
                metric_name="current",
                render_func=lambda x: "%0.1fA" % x,
                label="Current",
            )

register.check_plugin(
    name="enexus_battery_current",
    sections=["enexus_battery", 'enexus_status'],
    service_name="eNexus Battery %s",
    discovery_function=discover_enexus_battery_current,
    check_function=check_enexus_battery_current,
)