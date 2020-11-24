# -*- coding: utf-8 -*-

"""
This file contains the hardware control of the motorized stage for PI Micos.

Qudi is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Qudi is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Qudi. If not, see <http://www.gnu.org/licenses/>.

Copyright (c) the Qudi Developers. See the COPYRIGHT.txt file at the
top-level directory of this distribution and at <https://github.com/Ulm-IQO/qudi/>
"""

import visa
import time

from collections import OrderedDict

from core.module import Base
from core.configoption import ConfigOption
from interface.motor_interface import MotorInterface

from core.module import Base
from core.configoption import ConfigOption

class NPZactuator(Base, MotorInterface):
    """unstable: Jochen Scheuer.
    Hardware class to define the controls for the NPZ stage of Newport.
    """
    _modclass = 'NPZactuator'
    _modtype = 'hardware'

    _com_port = ConfigOption('com_port', 'COM4', missing='warn')
    _baud_rate = ConfigOption('baud_rate', 19200, missing='warn')
    _timeout = ConfigOption('timeout', 1000, missing='warn')
    _term_char = ConfigOption('term_char', '\r\n', missing='warn')

    _axis_label = ConfigOption('axis_label', 'x', missing='warn')

    _axis_ID = ConfigOption('axis_ID', '0', missing='warn')

    _min = ConfigOption('min', -10000000, missing='warn')
    _max = ConfigOption('max', 10000000, missing='warn')

    step_axis = ConfigOption('axis_step', 160e-9, missing='warn') #from documentation page 13/62

    _vel_min = ConfigOption('vel_min', 0, missing='warn')
    _vel_max = ConfigOption('vel_max', 48000, missing='warn')

    _vel_step = ConfigOption('vel_axis_step', 1e-8, missing='warn')

    #Todo: add term_char to visa connection

    def on_activate(self):
        """ Initialisation performed during activation of the module.
        @return: error code
        """
        self.rm = visa.ResourceManager()
        self._serial_connection = self.rm.open_resource(
            resource_name=self._com_port,
            baud_rate=self._baud_rate,
            timeout=self._timeout)

        constraints = self.get_constraints()
        all_axis_labels = [axis_label for axis_label in constraints]

        self.log.info('The unit is microstep - 1 microstep is about 10nm')

        # Setting hardware limits to the stage. The stage will not move further these limits!
        self._write('x', '{} {} setlimit'.format(constraints['x']['pos_min'],constraints['x']['pos_max']))

        self.log.info("Hardware limits were set to NPZ stage. To change the limits adjust the config file.")

        return 0

    def on_deactivate(self):
        """ Deinitialisation performed during deactivation of the module.
        @return: error code
        """
        self._serial_connection.close()
        self.rm.close()
        return 0

    def get_constraints(self):
        """ Retrieve the hardware constrains from the motor device.

        @return dict: dict with constraints for the sequence generation and GUI

        Provides all the constraints for the motorized stage (like total
        movement, velocity, ...)
        Each constraint is a tuple of the form
            (min_value, max_value, stepsize)

        The possible keys in the constraint are defined here in the interface
        file. If the hardware does not support the values for the constraints,
        then insert just None.
        If you are not sure about the meaning, look in other hardware files
        to get an impression.
        """
        constraints = OrderedDict()

        axis = {}
        axis['label'] = self._axis_label
        axis['ID'] = self._axis_ID
        axis['unit'] = 'step'  # the units
        axis['ramp'] = None  # a possible list of ramps
        axis['pos_min'] = self._min
        axis['pos_max'] = self._max
        axis['pos_step'] = self.step_axis
        axis['vel_min'] = self._vel_min
        axis['vel_max'] = self._vel_max
        axis['vel_step'] = self._vel_step
        axis['acc_min'] = None
        axis['acc_max'] = None
        axis['acc_step'] = None

        # assign the parameter container for x to a name which will identify it
        constraints[axis['label']] = axis

        return constraints

    def move_rel(self, param_dict):
        pass

    def move_abs(self, param_dict):
        pass

    def abort(self):
        pass

    def get_pos(self, param_list=None):
        pass

    def get_status(self, param_list=None):
        pass

    def calibrate(self, param_list=None):
        pass

    def get_velocity(self, param_list=None):
        pass

    def set_velocity(self, param_dict):
        pass

    def _write(self, axis, command):
        pass

    def _read_answer(self, axis):
        pass

    def _ask(self, axis, question):
        pass

    def _in_movement(self):
        pass

    def _motor_stopped(self):
        pass

    def _do_move_rel(self, axis, step):
        pass