# -*- coding: utf-8 -*-
"""
This module operates a confocal microscope based on a stepping hardware.

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

from qtpy import QtCore
from collections import OrderedDict
from copy import copy
import time
import datetime
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from io import BytesIO

from logic.generic_logic import GenericLogic


class ConfocalStepperLogic(GenericLogic):  # Todo connect to generic logic
    """
    This is the Logic class for confocal stepping.
    """
    _modclass = 'confocalsteppinglogic'
    _modtype = 'logic'

    _connectors = {
        'confocalstepper1': 'ConfocalStepperInterface',
        'savelogic': 'SaveLogic'
    }

    # Todo: add connectors adn QTCore Signals

    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)

        # counter for scan_image
        self._step_counter = 0
        self._zscan = False
        self.stopRequested = False
        self.depth_scan_dir_is_xz = True

    def on_activate(self):
        """ Initialisation performed during activation of the module.
        """
        self._stepping_device = self.get_connector('confocalstepper1')
        # Todo add connectors
        pass

    def on_deactivate(self):
        """ Reverse steps of activation

        @return int: error code (0:OK, -1:error)
        """
        pass

    def set_clock_frequency(self, clock_frequency):
        """Sets the frequency of the clock

        @param int clock_frequency: desired frequency of the clock

        @return int: error code (0:OK, -1:error)
        """
        self._clock_frequency = int(clock_frequency)
        # checks if scanner is still running
        if self.getState() == 'locked':
            return -1
        else:
            return 0

    def _check_freq(self, freq):
        pass

    ##################################### Control Stepper ########################################

    def start_stepper(self):
        """Starts the scanning procedure

        @return int: error code (0:OK, -1:error)
        """
        pass

    def continue_stepper(self):
        """Continue the stepping procedure

        @return int: error code (0:OK, -1:error)
        """
        pass

    def move_to_position(self, x=None, y=None, z=None):
        """Moving the stepping device (approximately) to the desired new position from the GUI.

        @param float x: if defined, changes to position in x-direction (steps)
        @param float y: if defined, changes to position in y-direction (steps)
        @param float z: if defined, changes to position in z-direction (steps)

        @return int: error code (0:OK, -1:error)
        """
        # Todo throw a waring, that without position feedback this is very imprecise

        #Check if freq and voltage are set as set in GUI

        if x is not None and x != self._current_x:
            out = True
            x_steps = x - self._current_x
            if (x_steps < 0):
                out = False
            return_value = self._stepping_device.move_attocube("x", True, out, steps=abs(x_steps))
            self._current_x = x

        if return_value == -1:
            return return_value

        if y is not None and y != self._current_y:
            out = True
            y_steps = y - self._current_y
            if (y_steps < 0):
                out = False
            return_value = self._stepping_device.move_attocube("y", True, out, steps=abs(y_steps))
            self._current_y = y

        if return_value == -1:
            return return_value

        if z is not None and z != self._current_z:
            up = True
            z_steps = z - self._current_z
            if (z_steps < 0):
                out = False
            return_value = self._stepping_device.move_attocube("z", True, out, steps=abs(z_steps))
            self._current_z = z

        return return_value

    def get_position(self):
        """ Get position from stepping device.

        @return list: with three entries x, y and z denoting the current
                      position in meters
        """
        pass
        # Todo this only works with position feedback hardware. Not sure if should be kept, as not possible for half the steppers

    def _scan(self):
        """Scans the image by scanning single lines and synchronising counter with it.

        """
        pass

    def _scan_line(self, axes, direction=True):
        """scanning a line in a given direction (up or down)
        @param str axes: the axes combination to be scanned
        @param bool direction: the direction in which the previous line was scanned

        @return bool: If true scan was in up direction, if false scan was in down direction
        """
        pass
        # Todo This needs to do the following things: scan a line with the given amount of steps and th

    def _step_and_count(self, axis, direction=True):

        self._stepping_device.move_attocube(axis, "stepping", "up", steps=self.steps_scanner)
        data = self._counting_device.start_counter()

        return data

    ##################################### Handle Data ########################################

    def initialize_image(self):
        """Initalization of the image.

        @return int: error code (0:OK, -1:error)
        """
        pass

    def save_xy_data(self, colorscale_range=None, percentile_range=None):
        """ Save the current confocal xy data to file.

        Two files are created.  The first is the imagedata, which has a text-matrix of count values
        corresponding to the pixel matrix of the image.  Only count-values are saved here.

        The second file saves the full raw data with x, y, z, and counts at every pixel.

        A figure is also saved.

        @param: list colorscale_range (optional) The range [min, max] of the display colour scale (for the figure)

        @param: list percentile_range (optional) The percentile range [min, max] of the color scale
        """
        # Todo Ask if it is possible to write only one save with options for which lines were scanned
        pass

    def draw_figure(self, data, image_extent, scan_axis=None, cbar_range=None,
                    percentile_range=None, crosshair_pos=None):
        """ Create a 2-D color map figure of the scan image for saving

        @param: array data: The NxM array of count values from a scan with NxM pixels.

        @param: list image_extent: The scan range in the form [hor_min, hor_max, ver_min, ver_max]

        @param: list axes: Names of the horizontal and vertical axes in the image

        @param: list cbar_range: (optional) [color_scale_min, color_scale_max].  If not supplied then a default of
                                 data_min to data_max will be used.

        @param: list percentile_range: (optional) Percentile range of the chosen cbar_range.

        @param: list crosshair_pos: (optional) crosshair position as [hor, vert] in the chosen image axes.

        @return: fig fig: a matplotlib figure object to be saved to file.
        """

        # Todo Probably the function from confocal logic, that already exists need to be chaned only slightly
        pass

    ##################################### Tilt correction ########################################


    @QtCore.Slot()
    def set_tilt_point1(self):
        """ Gets the first reference point for tilt correction."""
        pass
        self.point1 = np.array(self._scanning_device.get_scanner_position()[:3])
        self.signal_tilt_correction_update.emit()

    @QtCore.Slot()
    def set_tilt_point2(self):
        """ Gets the second reference point for tilt correction."""
        pass
        self.point2 = np.array(self._scanning_device.get_scanner_position()[:3])
        self.signal_tilt_correction_update.emit()

    @QtCore.Slot()
    def set_tilt_point3(self):
        """Gets the third reference point for tilt correction."""
        pass
        self.point3 = np.array(self._scanning_device.get_scanner_position()[:3])
        self.signal_tilt_correction_update.emit()

    @QtCore.Slot(bool)
    def set_tilt_correction(self, enabled):
        """ Set tilt correction in tilt interfuse.

            @param bool enabled: whether we want to use tilt correction
        """
        self._scanning_device.tiltcorrection = enabled
        self._scanning_device.tilt_reference_x = self._scanning_device.get_scanner_position()[
            0]
        self._scanning_device.tilt_reference_y = self._scanning_device.get_scanner_position()[
            1]
        self.signal_tilt_correction_active.emit(enabled)

        ##################################### Move through History ########################################

    def history_forward(self):
        """ Move forward in confocal image history.
        """
        pass
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.history[self.history_index].restore(self)
            self.signal_xy_image_updated.emit()
            self.signal_depth_image_updated.emit()
            self.signal_tilt_correction_update.emit()
            self.signal_tilt_correction_active.emit(self._scanning_device.tiltcorrection)
            self._change_position('history')
            self.signal_change_position.emit('history')
            self.signal_history_event.emit()

    def history_back(self):
        """ Move backwards in confocal image history.
        """
        pass
        if self.history_index > 0:
            self.history_index -= 1
            self.history[self.history_index].restore(self)
            self.signal_xy_image_updated.emit()
            self.signal_depth_image_updated.emit()
            self.signal_tilt_correction_update.emit()
            self.signal_tilt_correction_active.emit(self._scanning_device.tiltcorrection)
            self._change_position('history')
            self.signal_change_position.emit('history')
            self.signal_history_event.emit()