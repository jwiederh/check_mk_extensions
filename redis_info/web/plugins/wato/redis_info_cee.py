#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-

# Check_MK Redis Info Plugin 
#
# Copyright 2016, Clemens Steinkogler <c.steinkogler[at]cashpoint.com>
#
# Extended 2017, Robert Sander <r.sander@heinlein-support.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from cmk.gui.i18n import _
from cmk.gui.plugins.wato import (
    HostRulespec,
    rulespec_registry,
)
from cmk.gui.cee.plugins.wato.agent_bakery.rulespecs.utils import RulespecGroupMonitoringAgentsAgentPlugins
from cmk.gui.valuespec import (
    Alternative,
    CascadingDropdown,
    FixedValue,
    Integer,
    IPv4Address,
    ListOf,
    Password,
    Tuple,
)

def _valuespec_agent_config_redis_info():
    return CascadingDropdown(
        title = _("REDIS instances (Linux)"),
        help = _("If you activate this option, then the agent plugin <tt>redis_info</tt> will be deployed. "
                 "For each configured or detected REDIS instance there will be one new service with detailed "
                 "statistics of the current number of clients and processes and their various states."),
        # style = "dropdown",
        choices = [
            ( "autodetect", _("Autodetect instances"),
                Alternative(
                    style = "dropdown",
                    orientation = 'horizontal',
                    elements = [
                        FixedValue(None,
                            title = _("Don't use password"),
                            totext = _("no password"),
                        ),
                        Password(
                            title = _("Default Password"),
                        ),
                    ]
                ),
             ),
            ( "static", _("Specific list of instances"),
                Tuple(
                    elements = [
                        ListOf(
                            Tuple(
                                elements = [
                                    IPv4Address(
                                        title = _("IP Address"),
                                        default_value = "127.0.0.1",
                                    ),
                                    Alternative(
                                        style = "dropdown",
                                        orientation = 'horizontal',
                                        elements = [
                                            FixedValue(None,
                                                title = _("Don't use custom port"),
                                                totext = _("Use default port"),
                                            ),
                                            Integer(
                                                title = _("TCP Port Number"),
                                                minvalue = 1,
                                                maxvalue = 65535,
                                                default_value = 6379,
                                            ),
                                        ]
                                    ),
                                    Alternative(
                                        style = "dropdown",
                                        orientation = 'horizontal',
                                        elements = [
                                            FixedValue(None,
                                                title = _("Don't use custom password"),
                                                totext = _("Use default password"),
                                            ),
                                            Password(
                                                title = _("Password"),
                                            ),
                                        ]
                                    ),
                                ]
                            ),
                        ),
                        Alternative(
                            style = "dropdown",
                            orientation = 'horizontal',
                            elements = [
                                FixedValue(None,
                                    title = _("Don't use password"),
                                    totext = _("no password"),
                                ),
                                Password(
                                    title = _("Default Password"),
                                ),
                            ]
                        ),
                    ],
                ),
            ),
            ( '_no_deploy', _("Do not deploy the redis_info plugin") ),
        ]
    )

rulespec_registry.register(
     HostRulespec(
         group=RulespecGroupMonitoringAgentsAgentPlugins,
         name="agent_config:redis_info",
         valuespec=_valuespec_agent_config_redis_info,
     ))
