# -*- coding: utf-8 -*-
"""
This file contains the Qudi logic class that captures and processes fluorescence spectra.

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
import numpy as np
import matplot.pyplot as plt

from core.connector import Connector
from core.statusvariable import StatusVar
from core.util.mutex import Mutex
from core.util.network import netobtain
from logic.generic_logic import GenericLogic


class ShamrockLogic(GenericLogic):
    """This logic module gathers data from the spectrometer.
    """

    # declare connectors
    spectrometer = Connector(interface='SpectrometerInterface')
    camera = Connector(interface='camera_deviceInterface')

    # declare status variables
    _spectrum_data = StatusVar('spectrum_data', np.empty((2, 0)))
    _background_data = StatusVar('background_data', np.empty((2, 0)))
    _grating = StatusVar('grating', 1)
    _detector_offset = StatusVar('detector_offset', 0)
    _input_slit = StatusVar('input_slit', 1)
    _output_slit = StatusVar('output_slit', 0)
    _input_slit_width = StatusVar('input_slit_width', 100)
    _output_slit_width = StatusVar('output_slit_width', 100)

    # Internal signals
    sign_specdata_updated = QtCore.Signal()
    sig_next_diff_loop = QtCore.Signal()

    # External signals eg for GUI module
    spectrum_fit_updated_Signal = QtCore.Signal(np.ndarray, dict, str)
    fit_domain_updated_Signal = QtCore.Signal(np.ndarray)

    ##############################################################################
    #                            Basic functions
    ##############################################################################

    def __init__(self, **kwargs):
        """ Create SpectrometerLogic object with connectors.

          @param dict kwargs: optional parameters
        """
        super().__init__(**kwargs)

        # locking for thread safety
        self.threadlock = Mutex()

    def on_activate(self):
        """ Initialisation performed during activation of the module.
        """
        self.spectrometer_device = self.spectrometer()
        self.camera_device = self.camera()

        _center_wavelength = self.center_wavelength


    def on_deactivate(self):
        """ Deinitialisation performed during deactivation of the module.
        """
        if self.module_state() != 'idle' and self.module_state() != 'deactivated':
            pass


    ##############################################################################
    #                            Camera wrapper functions
    ##############################################################################

    @property
    def spectrum_data(self):
        return self._spectrum_data

    def acquire_spectrum(self):

        if self.camera_device.start_single_acquisition():
            self._spectrum_data = self.camera_device.get_acquired_data()
            self.log.info('Single spectrum acquisition achieved with success ')
            return 1
        else:
            self.log.info('Single spectrum acquisition aborted ')
            return 0


    ##############################################################################
    #                            Spectrometer wrapper functions
    ##############################################################################

    @property
    def grating(self):
        return self.spectrometer_device.get_grating()

    @grating.setter
    def grating(self,grating_number):
        parameter_correct = (type(grating_number) is int and 0<grating_number<4)
        if parameter_correct and grating_number != self._grating:
            self.spectrometer_device.set_grating(grating_number)
            self.log.info('Spectrometer grating has been changed correctly ')
            self._grating = grating_number
            return 1
        else:
            if not parameter_correct:
                self.log.debug('Grating parameter is not correct : it must be an integer ranging from 1 to 3 ')
            else:
                self.log.debug('Grating parameter is equal to the current grating used ')
            return 0

    @property
    def center_wavelength(self):
        return self.spectrometer_device.get_central_wavelength()

    @center_wavelength.setter
    def center_wavelength(self,wavelength):
        parameter_correct = type(wavelength) is (float or int)
        if parameter_correct and wavelength!= self._center_wavelength:
            self.spectrometer_device.set_central_wavelength(float(wavelength))
            self.log.info('Central wavelength has been changed correctly ')
            self._center_wavelength = wavelength
            return 1
        else:
            if not parameter_correct:
                self.log.debug('Wavelength parameter is not correct : it must be an integer or a float ')
            else:
                self.log.debug('Wavelength parameter is equal to the current central wavelength ')
            return 0

    @property
    def wavelength_limits(self):
        return self.spectrometer_device.get_wavelength_limits(self._grating)

    @property
    def detector_offset(self):
        return self.spectrometer_device.get_detector_offset()

    @detector_offset.setter
    def center_wavelength(self,offset):
        parameter_correct = type(offset) is int
        if parameter_correct and offset!= self._detector_offset:
            self.spectrometer_device.set_detector_offset(offset)
            self.log.info('Detector offset has been set correctly ')
            self._detector_offset = offset
            return 1
        else:
            if not parameter_correct:
                self.log.debug('Offset parameter is not correct : it must be an integer  ')
            else:
                self.log.debug('Offset parameter is equal to the actual detector offset ')
            return 0

    @property
    def input_slit(self):
        return self.spectrometer_device.get_flipper_mirror_position(0)

    @input_slit.setter
    def input_slit(self, position):
        parameter_correct = type(position) is int
        if parameter_correct and position != self._input_slit and -1<position<2:
            self.spectrometer_device.set_flipper_mirror_position(0,position)
            self.log.info('Input slit has been selected correctly ')
            self._input_slit = position
            return 1
        else:
            if not parameter_correct:
                self.log.debug('Slit selection parameter is not correct : it must be an integer ')
            else:
                self.log.debug('Slit selection parameter is equal to the current input slit ')
            return 0

    @property
    def output_slit(self):
        return self.spectrometer_device.get_flipper_mirror_position(1)

    @output_slit.setter
    def output_slit(self, position):
        parameter_correct = type(position) is int
        if parameter_correct and position != self._output_slit and -1<position<2:
            self.spectrometer_device.set_flipper_mirror_position(1,position)
            self.log.info('Output slit has been selected correctly ')
            self._output_slit = position
            return 1
        else:
            if not parameter_correct:
                self.log.debug('Slit selection parameter is not correct : it must be an integer ')
            else:
                self.log.debug('Slit selection parameter is equal to the current output slit ')
            return 0

    @property
    def input_slit_width(self):
        return self.spectrometer_device.get_auto_slit_width(0)

    @input_slit_width.setter
    def input_slit_width(self, width):
        parameter_correct = type(width) is float
        if parameter_correct and width != self._input_slit_width and 0 < width :
            self.spectrometer_device.set_auto_slit_width(0, width)
            self.log.info('Input slit width has been selected correctly ')
            self._input_slit_width = width
            return 1
        else:
            if not parameter_correct:
                self.log.debug('Slit selection parameter is not correct : it must be a float ')
            if 0 < width:
                self.log.debug('Slit width parameter is not correct : it must be positive ')
            else:
                self.log.debug('Slit selection parameter is equal to the current input slit width ')
            return 0

    @property
    def output_slit_width(self):
        return self.spectrometer_device.get_auto_slit_width(1)

    @output_slit_width.setter
    def output_slit_width(self, width):
        parameter_correct = type(width) is float
        if parameter_correct and width != self._output_slit_width and 0 < width:
            self.spectrometer_device.set_auto_slit_width(1, width)
            self.log.info('Output slit width has been selected correctly ')
            self._output_slit_width = width
            return 1
        else:
            if not parameter_correct:
                self.log.debug('Slit width parameter is not correct : it must be a float ')
            if 0 < width:
                self.log.debug('Slit width parameter is not correct : it must be positive ')
            else:
                self.log.debug('Slit width parameter is equal to the current output slit width ')
            return 0