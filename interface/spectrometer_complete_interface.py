# -*- coding: utf-8 -*-
"""
This module contains the spectrometer interface module based on the
Shamrock hardware module. This is an updated version of the spectrometer interface
which display more functional method.

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

from core.interface import abstract_interface_method
from core.meta import InterfaceMetaclass


class SpectrometerInterface(metaclass=InterfaceMetaclass):
    """This is the Interface class to define the controls for the simple
    optical spectrometer.
    """

    ##############################################################################
    #                            Gratings functions
    ##############################################################################

    @abstract_interface_method
    def set_grating(self, grating):
        pass

    @abstract_interface_method
    def get_grating(self):
        pass

    @abstract_interface_method
    def get_number_grating(self):
        pass

    ##############################################################################
    #                            Wavelength functions
    ##############################################################################

    @abstract_interface_method
    def set_wavelength(self, wavelength):
        pass

    @abstract_interface_method
    def get_wavelength(self):
        pass

    @abstract_interface_method
    def get_wavelength_limit(self, grating):
        pass

    @abstract_interface_method
    def goto_zero_order(self):
        pass

    @abstract_interface_method
    def at_zero_order(self):
        pass

