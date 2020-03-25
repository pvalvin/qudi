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
    _device = ConfigOption('device',missing='warn')

##############################################################################
#                            Basic functions
##############################################################################

    def error_message(self, error, function=''):
        if not error == 20202:
            print(f"{function}: {ERROR_CODE[error]}")
            return 0
        else:
            return 1

    def on_activate(self):

        self.dll = ct.cdll.LoadLibrary(_dll_location)

        error = self.dll.ShamrockInitialize()

        self.number_device = ct.c_int()
        self.dll.ShamrockGetNumberDevices(ct.byref(number_device))
        self.number_device = self.number_device.value

        return self.error_message(error, "Initialize")

    def on_deactivate(self):
        return self.dll.ShamrockClose()
        
##############################################################################
#                            Gratings functions
##############################################################################

    def set_grating(self, grating):
        if type(grating) is int :
            error = self.dll.ShamrockSetGrating(_device, grating)
            return self.error_message(error, "SetGrating")
        else:
            raise TypeError('set_grating function "grating" parameter needs to be int type')

    def get_grating(self):
        grating = 0
        error = self.dll.ShamrockGetGrating(_device, ct.byref(grating))
        self.error_message(error, "GetGrating")
        return grating

    def get_number_grating(self):
        grating_number = 0
        error = self.dll.ShamrockGetNumberGratings(_device, ct.byref(grating_number))
        self.error_message(error, "GetNumberGratings")
        return grating_number

    def get_grating_info(self, grating):
        lines = 0
        blaze = '     '.encode('UTF-8') # 5 chars long !
        home = 0
        offset = 0
        error = self.dll.ShamrockGetGratingInfo(_device, ct.byref(grating), ct.byref(lines), ct.byref(blaze)
                                                , ct.byref(home), ct.byref(offset))
        self.error_message(error, "GetGratingInfo")
        return lines, blaze, home, offset

##############################################################################
#                            Wavelength functions
##############################################################################

    def set_wavelength(self, wavelength):
        if type(wavelength) is float :
            error = self.dll.ShamrockSetWavelength(_device, wavelength)
            return self.error_message(error, "SetWavelength")
        else:
            raise TypeError('set_wavelength function "wavelength" parameter needs to be float type')

    def get_wavelength(self):
        wavelength = 0
        error = self.dll.ShamrockGetWavelength(_device, ct.byref(wavelength))
        self.error_message(error, "GetWavelength")
        return wavelength

    def get_wavelength_limit(self, grating):
        wavelength_min = 0
        wavelength_max = 0
        error = self.dll.ShamrockGetWavelengthLimits(_device, ct.byref(grating), ct.byref(wavelength_min)\
                                                     , ct.byref(wavelength_max))
        self.error_message(error, "GetWavelengthLimits")
        return wavelength_min, wavelength_max

##############################################################################
#                            Readout functions
##############################################################################

    # Pixels parameters :
    
    def set_pixel_width(self, width):
        if type(width) is float :
            error = self.dll.ShamrockSetPixelWidth(_device, width)
            return self.error_message(error, "SetPixelWidth")
        else:
            raise TypeError('set_pixel_width function "width" parameter needs to be int type')

    def set_number_pixel(self, pixel_number):
        if type(pixel_number) is int :
            error = self.dll.ShamrockSetNumberPixels(_device, pixel_number)
            return self.error_message(error, "SetNumberPixels")
        else:
            raise TypeError('set_pixel_width function "width" parameter needs to be int type')
     
    # Detector offset :
    
    def get_detector_offset(self):
        offset = 0
        error = self.dll.ShamrockGetDetectorOffset(_device, ct.byref(offset))
        self.error_message(error, "GetDetectorOffset")
        return offset

    def set_detector_offset(self, offset):
        if type(offset) is int :
            error = self.dll.ShamrockSetDetectorOffset(_device, ct.byref(offset))
            return self.error_message(error, "SetDetectorOffset")
        else :
            raise TypeError('set_detector_offset function "offset" parameter needs to be int type')
      
    # Detector calibration :
    
    def get_calibration(self, number_pixels):
        if type(number_pixels) is int :
            waves = np.empty(number_pixels,dtype=np.float32)
            error = self.dll.ShamrockGetCalibration(_device, ct.byref(waves.data), ct.byref(number_pixels))
            self.error_message(error, "GetCalibration")
            return waves
        else:
            raise TypeError('get_calibration function "number_pixels" parameter needs to be int type')

    def set_flipper_mirror_position(self, flipper, position):
        if type(flipper) is int :
            if type(position) is float :
                error = self.dll.ShamrockSetFlipperMirrorPosition(_device, flipper, position)
                return self.error_message(error, "SetFlipperMirrorPosition")
            else: 
                raise TypeError('set_flipper_mirror_position function "position" parameter needs to be float type')
        else:
            raise TypeError('set_flipper_mirror_position function "flipper" parameter needs to be float type')


    def get_flipper_mirror_position(self, flipper):
        if type(flipper) is int:
            position = 0
            error = self.dll.ShamrockGetFlipperMirrorPosition(_device, flipper, ct.byref(position))
            self.error_message(error, "GetFlipperMirrorPosition")
            return position
        else:
            raise TypeError('get_flipper_mirror_position function "flipper" parameter needs to be float int')

    def set_auto_slit_width(self, index, width): # width in um !
        if type(index) is int:
            if type(width) is float:
                error = self.dll.ShamrockSetAutoSlitWidth(_device, index, width)
                return self.error_message(error, "SetAutoSlitWidth")
            else:
                raise TypeError('set_auto_slit_width function "width" parameter needs to be float type')
        else:
            raise TypeError('set_auto_slit_width function "index" parameter needs to be float int')

    def get_auto_slit_width(self, index):
        if type(index) is int:
            width = 0
            error = self.dll.ShamrockGetAutoSlitWidth(_device, index, ct.byref(width))
            self.error_message(error, "GetAutoSlitWidth")
            return w # w in um !
        else:
            raise TypeError('get_auto_slit_width function "index" parameter needs to be int type')

    #unsigned int ShamrockGetGratingOffset(int device,int Grating, int *offset)
    def get_grating_offset(self, grating):
        if type(grating) is int:
            offset = 0
            error = self.dll.ShamrockGetGratingOffset(_device, grating, ct.byref(offset))
            self.error_message(error, "GetGratingOffset")
            return offset
        else: 
            raise TypeError('get_grating_offset function "grating" parameter needs to be int type')

    #unsigned int ShamrockSetGratingOffset(int device,int Grating, int offset)
    def set_grating_offset(self, grating, offset):
        if type(grating) is int:
            if type(offset) is float:
                error = self.dll.ShamrockSetGratingOffset(_device, grating, offset)
                return self.error_message(error, "SetGratingOffset")
            else:
                raise TypeError('set_grating_offset function "offset" parameter needs to be float type')
        else:
            raise TypeError('set_grating_offset function "grating" parameter needs to be int type')


    def goto_zero_order(self):
        error = self.dll.ShamrockGotoZeroOrder(_device)
        return self.error_message(error, "GotoZeroOrder")

    def at_zero_order(self):
        zero_order = 0
        error = self.dll.ShamrockAtZeroOrder(_device, ct.byref(zero_order))
        self.error_message(error, "AtZeroOrder")
        return zero_order



    
    
    