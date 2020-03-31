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


    def on_activate(self):
        """ Activate module.
        """
        self.spectrometer_status = 0
        self.errorcode = self._create_errorcode()

        self.dll = ct.cdll.LoadLibrary('C:/temp/ShamrockCIF.dll')
        code = self.dll.ShamrockInitialize()

        if code!=20202:
            self.log.info('Problem during spectrometer initialization')
            self.on_deactivate()
        else:
            self.spectrometer_status = 1
            nd = ct.c_int()
            self.dll.ShamrockGetNumberDevices(ct.byref(nd))
            #self.nd = nd.value
            self.deviceID = 0 #hard coding : whatever the number of devices... we work with the first. Fix me ?
            self.gratingID = self.get_grating()

    def on_deactivate(self):
        return self.dll.ShamrockClose()

    def check(self, func_val):
        """ Check routine for the received error codes.
        """

        if not func_val == 20202:
            self.log.error('Error in Shamrock with errorcode {0}:\n'
                           '{1}'.format(func_val, self.errorcode[func_val]))
        return func_val

    def _create_errorcode(self):
        """ Create a dictionary with the errorcode for the device.
        """

        maindir = get_main_dir()

        filename = os.path.join(maindir, 'hardware', 'spectrometer', 'errorcodes_shamrock.h')
        try:
            with open(filename) as f:
                content = f.readlines()
        except:
            self.log.error('No file "errorcodes_shamrock.h" could be found in the '
                        'hardware/spectrometer directory!')

        errorcode = {}
        for line in content:
            if '#define SHAMROCK' in line:
                errorstring, errorvalue = line.split()[-2:]
                errorcode[int(errorvalue)] = errorstring

        return errorcode

    def get_number_device(self):
        """
        Returns the number of devices
        Tested : yes
        """
        number_of_devices = ct.c_int()
        self.check(self.dll.ShamrockGetNumberDevices(self.deviceID, ct.byref(number_of_devices)))
        return number_of_devices.value
        
##############################################################################
#                            Gratings functions
##############################################################################

    def get_grating(self):
        """
        Returns the current grating identification (1 to 3)
        Tested : yes
        """
        grating = ct.c_int()
        self.check(self.dll.ShamrockGetGrating(self.deviceID, ct.byref(grating)))
        return grating.value-1

    def set_grating(self, grating):
        """
        Sets the required grating

        @param int grating: grating identification number
        @return: void
        To be tested
        """
        if type(grating) is int :
            self.check(self.dll.ShamrockSetGrating(self.deviceID, grating))
        else:
            self.log.debug('set_grating function "grating" parameter needs to be int type')

    def get_number_grating(self):
        """
        Returns the number of gratings in the spectrometer

        @return int number_of_gratings

        Tested : yes
        """
        number_of_gratings = ct.c_int()
        self.check(self.dll.ShamrockGetNumberGratings(self.deviceID, ct.byref(number_of_gratings)))
        return number_of_gratings.value

    def get_grating_info(self, grating):
        """
        Returns grating informations

        @param int grating: grating id
        @return float line (line/mm), char* blaze (blaze wavelength in nm for 1st order),
            int home (steps), int offset (steps)

        Tested : yes
        """
        line = ct.c_float()
        blaze = ct.create_string_buffer(32)
        home = ct.c_int()
        offset = ct.c_int()
        self.check(self.dll.ShamrockGetGratingInfo(self.deviceID, grating,
                                                   ct.byref(line),
                                                   ct.byref(blaze),
                                                   ct.byref(home),
                                                   ct.byref(offset)))
        return line.value, blaze.value, home.value, offset.value

    def get_grating_offset(self, grating):
        """
        To be tested
        """
        if type(grating) is int:
            grating_offset = ct.c_int()
            self.check(self.dll.ShamrockGetGratingOffset(self.deviceID, grating, ct.byref(grating_offset)))
            return grating_offset.value
        else:
            self.log.debug('get_grating_offset function "grating" parameter needs to be int type')

    def set_grating_offset(self, grating, offset):
        """
        To be Tested !!
        """
        if type(grating) is int:
            if type(offset) is int:
                self.check(self.dll.ShamrockSetGratingOffset(self._deviceID, grating, offset))
            else:
                self.log.debug('set_grating_offset function "offset" parameter needs to be int type')
        else:
            self.log.debug('set_grating_offset function "grating" parameter needs to be int type')

##############################################################################
#                            Wavelength functions
##############################################################################

    def get_wavelength(self):
        """
        To be tested
        """
        wavelength = ct.c_float()
        self.check(self.dll.ShamrockGetWavelength(self.deviceID, ct.byref(wavelength)))
        return wavelength.value

    def set_wavelength(self, wavelength):
        """
        To be tested
        """
        if type(wavelength) is float :
            self.check(self.dll.ShamrockSetWavelength(self.deviceID, wavelength))
        else:
            self.log.debug('set_wavelength function "wavelength" parameter needs to be float type')
        return

    def get_wavelength_limit(self, grating):
        """
        To be tested
        """
        wavelength_min = ct.c_float()
        wavelength_max = ct.c_float()
        error = self.dll.ShamrockGetWavelengthLimits(self._device, grating, ct.byref(wavelength_min)
                                                     , ct.byref(wavelength_max))
        self.error_message(error, "GetWavelengthLimits")
        return wavelength_min.value, wavelength_max.value

    def goto_zero_order(self):
        """
        To be tested
        """
        self.check(self.dll.ShamrockGotoZeroOrder(self.deviceID))
        return

    def at_zero_order(self):
        """
        To be tested
        """
        zero_order = ct.c_int()
        self.check(self.dll.ShamrockAtZeroOrder(self.deviceID, ct.byref(zero_order)))
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

    def get_input_port(self):
        """
        Returns the current port for the input flipper mirror.
        Tested : yes
        """
        input_port = ct.c_int()
        if self.shamrock_flipper_mirror_is_present(2) == 1:
            self.check(self.dll.ShamrockGetFlipperMirror(self.deviceID, 1, ct.byref(input_port)))
            return input_port.value
        else:
            return 0

    def get_output_port(self):
        """
        Returns the current port for the output flipper mirror.
        Tested : yes
        """
        output_port = ct.c_int()
        if self.shamrock_flipper_mirror_is_present(2)==1:
            self.check(self.dll.ShamrockGetFlipperMirror(self.deviceID, 2, ct.byref(output_port)))
            return output_port.value
        else:
            return 0

    def set_input_port(self, input_port):

        if type(input_port) is int :
            self.check(self.dll.ShamrockSetFlipperMirror(self.deviceID, 1, input_port))
        else:
            self.log.debug('set_input_port function "input_port" parameter needs to be int type')
        return 0

    def set_output_port(self, output_port):

        if type(output_port) is int:
            self.check(self.dll.ShamrockSetFlipperMirror(self.deviceID, 2, output_port))
        else:
            self.log.debug('set_output_port function "output_port" parameter needs to be int type')
        return 0

    def set_auto_slit_width(self, slit_index, slit_width):

        if type(slit_index) is int:
            if type(slit_width) is float:
                self.check(self.dll.ShamrockSetAutoSlitWidth(self.deviceID, slit_index, slit_width))
            else:
                self.log.debug('set_auto_slit_width function "slit_width" parameter needs to be float type')
        else:
            self.log.debug('set_auto_slit_width function "slit_index" parameter needs to be int type')
        return 0

    def get_auto_slit_width(self, slit_index):
        """
                Returns the input slit width (um) in case of a motorized slit, -1 instead
                tested : yes
        """
        slit_width = ct.c_float()
        if self.shamrock_auto_slit_is_present(slit_index) == 1:
            self.check(self.dll.ShamrockGetAutoSlitWidth(self.deviceID, slit_index, ct.byref(slit_width)))
            return slit_width.value
        else:
            return -1

##############################################################################
#                            Shamrock wrapper
##############################################################################
# sdk basic functions

    def shamrock_flipper_mirror_is_present(self, flipper):
        present = ct.c_int()
        self.check(self.dll.ShamrockFlipperMirrorIsPresent(self.deviceID, flipper, ct.byref(present)))
        return present.value

    def shamrock_initialize(self):
        self.check(self.dll.ShamrockInitialize())
        return

    def shamrock_close(self):
        self.check(self.dll.ShamrockClose())
        return

    def shamrock_get_number_of_devices(self):
        """
        Returns the number of devices
        Tested : yes
        """
        number_of_devices = ct.c_int()
        self.check(self.dll.ShamrockGetNumberDevices(self.deviceID, ct.byref(number_of_devices)))
        return number_of_devices.value

    def shamrock_get_serial_number(self):
        """
        Returns the spectrometer serial number
        Tested : qudi crashes when executing the function. code commented
        """
        # serial = ct.create_string_buffer(64)
        # self.dll.ShamrockGetSerialNumber.argtypes = [ct.c_int32, ct.c_void_p]
        # self.check(self.dll.ShamrockGetSerialNumber(self.deviceID, ct.byref(serial)))
        # return serial.value.decode()
        pass

    def shamrock_get_optical_parameters(self):
        """
        Returns the spectrometer optical parameters

        @return float focal_length, float angular_deviation, float focal_tilt

        Tested :  yes
        """
        focal_length = ct.c_float()
        angular_deviation = ct.c_float()
        focal_tilt = ct.c_float()
        self.check(self.dll.ShamrockEepromGetOpticalParams(self.deviceID,\
                                                           ct.byref(focal_length),\
                                                           ct.byref(angular_deviation),\
                                                           ct.byref(focal_tilt) ))
        return focal_length.value, angular_deviation.value, focal_tilt.value

    def shamrock_get_number_gratings(self):
        """
        Returns the number of gratings in the spectrometer

        @return int number_of_gratings

        Tested : yes
        """
        number_of_gratings = ct.c_int()
        self.check(self.dll.ShamrockGetNumberGratings(self.deviceID, ct.byref(number_of_gratings)))
        return number_of_gratings.value

    def shamrock_grating_is_present(self):
        """
        Finds if grating is present

        @returns int 1 if present 0 if not

        Tested : yes
        """
        present = ct.c_int()
        self.check(self.dll.ShamrockGratingIsPresent(self.deviceID, ct.byref(present)))
        return present.value

    def shamrock_auto_slit_is_present(self, slit_index):
        present = ct.c_int()
        self.check(self.dll.ShamrockAutoSlitIsPresent(self.deviceID, slit_index, ct.byref(present)))
        return present.value

    def shamrock_get_detector_offset(self):
        offset = ct.c_int()
        self.check(self.dll.ShamrockGetDetectorOffset(self.deviceID, ct.byref(offset)))
        return offset.value

    def shamrock_get_grating_info(self, grating):
        """
        Returns grating informations

        @param int grating: grating id
        @return float line (line/mm), char* blaze (blaze wavelength in nm for 1st order),
            int home (steps), int offset (steps)

        Tested : yes
        """
        line = ct.c_float()
        blaze = ct.create_string_buffer(32)
        home = ct.c_int()
        offset = ct.c_int()
        self.check(self.dll.ShamrockGetGratingInfo(self.deviceID, grating,\
                                                   ct.byref(line),\
                                                   ct.byref(blaze),\
                                                   ct.byref(home),\
                                                   ct.byref(offset)))
        return line.value, blaze.value, home.value, offset.value

    def get_wavelength_limits(self, grating):
        lambda_min = ct.c_float()
        lambda_max = ct.c_float()
        self.check(self.dll.ShamrockGetWavelengthLimits(self.deviceID, grating, ct.byref(lambda_min), ct.byref(lambda_max)))
        return lambda_min.value, lambda_max.value

    def get_grating_offset(self, grating):
        grating_offset = ct.c_int()
        self.check(self.dll.ShamrockGetGratingOffset(self.deviceID, grating, ct.byref(grating_offset)))
        return grating_offset.value

    def shamrock_get_calibration(self, number_of_pixels):
        cal_values = np.ones((number_of_pixels,), dtype=np.float)
        self.dll.ShamrockGetCalibration.argtypes = [ct.c_int32, ct.c_float, ct.c_int32]
        self.check(self.dll.ShamrockGetCalibration(self.deviceID, cal_values.ctypes.data, number_of_pixels))
        return cal_values

    def shamrock_get_pixel_width(self):
        pixel_width = ct.c_float()
        self.check(self.dll.ShamrockGetPixelWidth(self.deviceID, ct.byref(pixel_width)))
        return pixel_width.value

    def get_pixel_width(self):
        pixel_width = ct.c_float()
        self.check(self.dll.ShamrockGetPixelWidth(self.deviceID, ct.byref(pixel_width)))
        return pixel_width.value

    def set_pixel_width(self, pixel_width):
        """Sets the pixel width( in microns) of the attached sensor. This is necessary for the dll to calculate a calibration
        """
        self.check(self.dll.ShamrockSetPixelWidth(self.deviceID, pixel_width))

    def get_pixels_number(self):
        pixels_number = ct.c_int()
        self.check(self.dll.ShamrockGetNumberPixels(self.deviceID, ct.byref(pixels_number)))
        return pixels_number.value

    def set_pixels_number(self, pixels_number):
        """Sets the pixels number of the attached sensor. This is necessary for the dll to calculate a calibration
        """
        self.check(self.dll.ShamrockSetNumberPixels(self.deviceID, pixels_number))
