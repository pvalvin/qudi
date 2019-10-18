# -*- coding: utf-8 -*-
"""
Interface for a spectrometer.

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


class L2CSpectrometerInterface(metaclass=InterfaceMetaclass):
    """
    This is the Interface class to define the controls for an optical spectrometer.
    """

    @abstract_interface_method
    def get_spectrometer_constraints(self):
        """
        constrains['gratings'] = [{'ruling': float,\
                                    'blaze': string,\
                                    'wavelength_min': float,\
                                    'wavelength_max': float},\
                                     ... ] - array size is number_of_gratings
        constraints['input_ports'] = int number of input ports
        constraints['output_ports'] = int number of input ports
        constraints['input_slits'] = [{'is_present': bool, 'max_slit_width': int}, ...] - array size is number_of_input_port
        constraints['output_slits'] = [{'is_present': bool, 'max_slit_width': int}, ...] - array size is number_of_input_port
        """
        pass

    def set_grating(self, grating):
        """
        Sets a new grating (grating is an int value between 0 and len[gratings]-1)
        """
        pass

    @abstract_interface_method
    def set_input_slit_width(self, input_slit_width):
        """
        Sets a new slit width (um) for input_port\
         (int value between 10 and max_slit_width)
        """
        pass

    @abstract_interface_method
    def set_output_slit_width(self, output_slit_width):
        """
        Sets a new slit width (um) for output_port\
         (int value between 10 and max_slit_width)
        """
        pass

    @abstract_interface_method
    def set_input_port(self, input_port):
        """
        Sets a new input port number (int value between 0 and max_output_port-1)
        """
        pass

    @abstract_interface_method
    def set_output_port(self, output_port):
        """
        Sets a new input port number (int value between 0 and max_output_port-1)
        """
        pass

    @abstract_interface_method
    def set_central_wavelength(self, lambda0):
        pass

    @abstract_interface_method
    def set_delta_lambda(self, delta_lambda):
        pass

###############################################

    @abstract_interface_method
    def get_spectrometer_id(self, spectrometer_id):
        """
        Returns the spectrometer serial number
        """
        pass

    def get_grating(self):
        """
        Returns the current grating identification (0 to len[gratings]-1)
        """
        pass

    @abstract_interface_method
    def get_input_slit_width(self, input_port):
        """
        Returns the current slit width (um) for param input_port\
         (int value between 10 and max_slit_width)
        """
        pass

    @abstract_interface_method
    def get_output_slit_width(self, output_port):
        """
        Returns the current slit width (um) for param output_port\
         (int value between 10 and max_slit_width)
        """
        pass

    @abstract_interface_method
    def get_input_port(self):
        """
        Returns the current output port number (int value between 0 and max_output_port-1)
        """
        pass

    @abstract_interface_method
    def get_output_port(self):
        """
        Returns the current output port number (int value between 0 and max_output_port-1)
        """
        pass

    @abstract_interface_method
    def get_central_wavelength(self):
        """
        Returns the current central wavelength (nm)
        (float value between wavelength_min and wavelength_max)
        """
        pass

    @abstract_interface_method
    def get_delta_lambda(self):
        pass

    @abstract_interface_method
    def get_spectrometer_status(self):
        """
        Returns a int code corresponding to the spectrometer status :
        0 : not initialized
        1 : initialized and ready (Idle)
        2 : busy (turret or grating is turning - set_grating or set_central_wavelength)
        """
        pass


