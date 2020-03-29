# -*- coding: utf-8 -*-
"""
This module contains the hardware module of the Shamrock 500
spectrometer from Andor.

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

from core.module import Base
from interface.spectrometer_complete_interface import SpectrometerInterface
from core.configoption import ConfigOption
from core.util.modules import get_main_dir
import os

import numpy as np

import ctypes as ct
import time

ERROR_CODE = {
    20201: "SHAMROCK_COMMUNICATION_ERROR",
    20202: "SHAMROCK_SUCCESS",
    20266: "SHAMROCK_P1INVALID",
    20267: "SHAMROCK_P2INVALID",
    20268: "SHAMROCK_P3INVALID",
    20269: "SHAMROCK_P4INVALID",
    20270: "SHAMROCK_P5INVALID",
    20275: "SHAMROCK_NOT_INITIALIZED"
}

class Shamrock(Base,SpectrometerInterface):

    _dll_location = ConfigOption('dll_location',missing='error')

##############################################################################
#                            Basic functions
##############################################################################

    def error_message(self, error, function=''):
        if not error == 20202:
            self.log.error(f"{function}: {ERROR_CODE[error]}")
            return 0
        else:
            return 1

    def on_activate(self):

        self.dll = ct.cdll.LoadLibrary(self._dll_location)

        error = self.dll.ShamrockInitialize()

        return self.error_message(error, "Initialize")

    def on_deactivate(self):
        return self.dll.ShamrockClose()

    def get_number_device(self):
        number_device = ct.c_int()
        error = self.dll.ShamrockGetNumberDevices(ct.byref(number_device))
        self.error_message(error, "GetNumberDevice")
        return number_device.value
        
##############################################################################
#                            Gratings functions
##############################################################################

    def get_grating(self):
        grating = ct.c_int()
        error = self.dll.ShamrockGetGrating(self._device, ct.byref(grating))
        self.error_message(error, "GetGrating")
        return grating.value

    def set_grating(self, grating):
        if type(grating) is int :
            error = self.dll.ShamrockSetGrating(self._device, grating)
            return self.error_message(error, "SetGrating")
        else:
            self.log.debug('set_grating function "grating" parameter needs to be int type')

    def get_number_grating(self):
        grating_number = ct.c_int()
        error = self.dll.ShamrockGetNumberGratings(self._device, ct.byref(grating_number))
        self.error_message(error, "GetNumberGratings")
        return grating_number.value

    def get_grating_info(self, grating):
        lines = ct.c_float()
        blaze = ct.create_string_buffer(32) # ct.c_char('     '.encode('UTF-8'))  5 chars long !
        home = ct.c_int()
        offset = ct.c_int()
        error = self.dll.ShamrockGetGratingInfo(self._device, ct.byref(grating), ct.byref(lines), ct.byref(blaze)
                                                , ct.byref(home), ct.byref(offset))
        self.error_message(error, "GetGratingInfo")
        return lines.value, blaze.value, home.value, offset.value

    #unsigned int ShamrockGetGratingOffset(int device,int Grating, int *offset)
    def get_grating_offset(self, grating):
        if type(grating) is int:
            offset = ct.c_int()
            error = self.dll.ShamrockGetGratingOffset(self._device, grating, ct.byref(offset))
            self.error_message(error, "GetGratingOffset")
            return offset.value
        else:
            self.log.debug('get_grating_offset function "grating" parameter needs to be int type')

    #unsigned int ShamrockSetGratingOffset(int device,int Grating, int offset)
    def set_grating_offset(self, grating, offset):
        if type(grating) is int:
            if type(offset) is int:
                error = self.dll.ShamrockSetGratingOffset(self._device, grating, offset)
                return self.error_message(error, "SetGratingOffset")
            else:
                self.log.debug('set_grating_offset function "offset" parameter needs to be int type')
        else:
            self.log.debug('set_grating_offset function "grating" parameter needs to be int type')

##############################################################################
#                            Wavelength functions
##############################################################################

    def get_wavelength(self):
        wavelength = ct.c_float()
        error = self.dll.ShamrockGetWavelength(self._device, ct.byref(wavelength))
        self.error_message(error, "GetWavelength")
        return wavelength.value

    def set_wavelength(self, wavelength):
        if type(wavelength) is float :
            error = self.dll.ShamrockSetWavelength(self._device, wavelength)
            return self.error_message(error, "SetWavelength")
        else:
            self.log.debug('set_wavelength function "wavelength" parameter needs to be float type')

    def get_wavelength_limit(self, grating):
        wavelength_min = ct.c_float()
        wavelength_max = ct.c_float()
        error = self.dll.ShamrockGetWavelengthLimits(self._device, grating, ct.byref(wavelength_min)
                                                     , ct.byref(wavelength_max))
        self.error_message(error, "GetWavelengthLimits")
        return wavelength_min.value, wavelength_max.value

    def goto_zero_order(self):
        error = self.dll.ShamrockGotoZeroOrder(self._device)
        return self.error_message(error, "GotoZeroOrder")

    def at_zero_order(self):
        zero_order = ct.c_int()
        error = self.dll.ShamrockAtZeroOrder(self._device, ct.byref(zero_order))
        self.error_message(error, "AtZeroOrder")
        return zero_order.value

##############################################################################
#                            Detector functions
##############################################################################

    # Pixels parameters :
    
    def set_pixel_width(self, width):
        if type(width) is float :
            error = self.dll.ShamrockSetPixelWidth(self._device, width)
            return self.error_message(error, "SetPixelWidth")
        else:
            self.log.debug('set_pixel_width function "width" parameter needs to be int type')

    def get_pixel_width(self):
        width = ct.c_float()
        error = self.dll.ShamrockGetPixelWidth(self._device, ct.byref(width))
        self.error_message(error, "ShamrockGetPixelWidth")
        return width.value

    def set_number_pixel(self, pixel_number):
        if type(pixel_number) is int :
            error = self.dll.ShamrockSetNumberPixels(self._device, pixel_number)
            return self.error_message(error, "SetNumberPixels")
        else:
            self.log.debug('set_pixel_width function "width" parameter needs to be int type')

    def get_number_pixel(self):
        pixel_number = ct.c_int()
        error = self.dll.ShamrockGetNumberPixels(self._device, ct.byref(pixel_number))
        self.error_message(error, "ShamrockGetNumberPixels")
        return pixel_number.value
     
    # Detector offset :
    
    def get_detector_offset(self):
        offset = ct.c_int()
        error = self.dll.ShamrockGetDetectorOffset(self._device, ct.byref(offset))
        self.error_message(error, "GetDetectorOffset")
        return offset.value

    def set_detector_offset(self, offset):
        if type(offset) is int :
            error = self.dll.ShamrockSetDetectorOffset(self._device, offset)
            return self.error_message(error, "SetDetectorOffset")
        else :
            self.log.debug('set_detector_offset function "offset" parameter needs to be int type')
      
    # Detector calibration :
    
    def get_calibration(self, number_pixels):
        if type(number_pixels) is int :
            value = ct.c_float()
            error = self.dll.ShamrockGetCalibration(self._device, ct.byref(value), number_pixels)
            self.error_message(error, "GetCalibration")
            return value.value
        else:
            self.log.debug('get_calibration function "number_pixels" parameter needs to be int type')

##############################################################################
#                            Slits functions
##############################################################################

    def set_flipper_mirror_position(self, flipper, position):
        if type(flipper) is int :
            if type(position) is int :
                error = self.dll.ShamrockSetFlipperMirrorPosition(self._device, flipper, position)
                return self.error_message(error, "SetFlipperMirrorPosition")
            else: 
                self.log.debug('set_flipper_mirror_position function "position" parameter needs to be int type')
        else:
            self.log.debug('set_flipper_mirror_position function "flipper" parameter needs to be int type')


    def get_flipper_mirror_position(self, flipper):
        if type(flipper) is int:
            position = ct.c_int()
            error = self.dll.ShamrockGetFlipperMirrorPosition(self._device, flipper, ct.byref(position))
            self.error_message(error, "GetFlipperMirrorPosition")
            return position.value
        else:
            self.log.debug('get_flipper_mirror_position function "flipper" parameter needs to be int type')

    def set_auto_slit_width(self, index, width): # width in um !
        if type(index) is int:
            if type(width) is float:
                error = self.dll.ShamrockSetAutoSlitWidth(self._device, index, width)
                return self.error_message(error, "SetAutoSlitWidth")
            else:
                self.log.debug('set_auto_slit_width function "width" parameter needs to be float type')
        else:
            self.log.debug('set_auto_slit_width function "index" parameter needs to be int type')

    def get_auto_slit_width(self, index):
        if type(index) is int:
            width = ct.c_float()
            error = self.dll.ShamrockGetAutoSlitWidth(self._device, index, ct.byref(width))
            self.error_message(error, "GetAutoSlitWidth")
            return width.value # w in um !
        else:
            self.log.debug('get_auto_slit_width function "index" parameter needs to be int type')
