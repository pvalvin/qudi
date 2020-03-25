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

# 1. Les default value, je les met où ?


class ShamrockLogic(GenericLogic):
    """This logic module gathers data from the spectrometer.
    """

    # declare connectors
    spectrometer_connector = Connector(interface='spectrometer')
    camera_connector = Connector(interface='camera')

    # declare status variables
    _spectrum_data = StatusVar('spectrum_data', np.empty((2, 0)))
    _grating = StatusVar('grating', 1)
    _central_wavelength = StatusVar('central_wavelength', 1.55)

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

        self.spectrometer = self.spectrometer_connector()
        self.camera = self.camera_connector()


    def on_deactivate(self):
        """ Deinitialisation performed during deactivation of the module.
        """
        if self.module_state() != 'idle' and self.module_state() != 'deactivated':
            pass

    ##############################################################################
    #                            Acquisition functions
    ##############################################################################

    def acquire_single_spectrum(self):

        if self.camera.start_single_acquisition():
            self.spectrum_data = self.camera.get_acquired_data()
            self.log.info('Single spectrum acquisition achived with success ')
            return 1
        else:
            self.log.info('Single spectrum acquisition aborted ')
            return 0

    ##############################################################################
    #                            Spectrometer wrapper functions
    ##############################################################################

    @property
    def grating(self):
        return self.spectrometer.get_grating()

    @grating.setter
    def grating(self,grating_number):
        parameter_correct = (type(grating_number) is int and 0<grating_number<4)
        if parameter_correct and grating_number!= self.grating:
            self.spectrometer.set_grating(grating_number)
            self.log.info('Spectrometer grating has been changed correctly ')
            return 1
        else:
            if not parameter_correct:
                self.log.debug('Grating parameter is not correct : it must be an integer ranging from 1 to 3 ')
            else:
                self.log.debug('Grating parameter is equal to the current grating used ')
            return 0

    @property
    def central_wavelength(self):
        return self.spectrometer.get_central_wavelength()

    @central_wavelength.setter
    def central_wavelength(self,wavelength):
        parameter_correct = type(wavelength) is (float or int)
        if parameter_correct and wavelength!= self.central_wavelength:
            self.spectrometer.set_central_wavelength(wavelength)
            self.log.info('Central wavelength has been changed correctly ')
            return 1
        else:
            if not parameter_correct:
                self.log.debug('Wavelength parameter is not correct : it must be an integer or a float ')
            else:
                self.log.debug('Wavelength parameter is equal to the current central wavelength ')
            return 0



    ##############################################################################
    #                            Camera wrapper functions
    ##############################################################################

    @property
    def spectrum_data(self):
        return self._spectrum_data