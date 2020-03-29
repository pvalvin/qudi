# -*- coding: utf-8 -*-


import ctypes as ct
import os
import time

import numpy as np

from core.configoption import ConfigOption
from core.module import Base
from core.util.modules import get_main_dir
from interface.spectrometer_interface import SpectrometerInterface


class Shamrock(Base, SpectrometerInterface):

    _dll_location = ConfigOption('dll_location', missing='error')

    ##############################################################################
    #                            Basic functions
    ##############################################################################

    def on_activate(self):
        """ Activate module.
        """
        self.errorcode = self._create_errorcode()

        self.dll = ct.cdll.LoadLibrary(self._dll_location) # adresse du fichier .dll dans le fichier .cfg
        self.dll.ShamrockInitialize()

        nd = ct.c_int()
        self.dll.ShamrockGetNumberDevices(ct.byref(nd))
        self.nd = nd.value
        self.deviceID = 0
        self.gratingID = self.get_gratingID()


    def on_deactivate(self):
        """ Deactivate module.
        """
        self.dll.ShamrockClose()
        pass

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


############### functions necessary for L2Cspectro_interface ##########################



    def get_grating(self):
        grating = ct.c_int()
        self.check(self.dll.ShamrockGetGrating(self.deviceID, ct.byref(grating)))
        return grating.value

    def get_central_wavelength(self):
        lambda0 = ct.c_float()
        self.check(self.dll.ShamrockGetWavelength(self.deviceID, ct.byref(lambda0)))
        return lambda0.value

    def get_input_port(self, input_port):
        pass

    def get_output_port(self, output_port):
        pass

    def get_input_slit_width(self, input_slit_width):
        pass

    def get_output_slit_width(self, output_slit_width):
        pass

    def get_delta_lambda(self, delta_lambda):
        pass

    def get_spectrometer_status(self, spectrometer_status):
        pass



    def set_grating(self):
        pass

    def set_central_wavelength(self, wavelength):
        minwl, maxwl = self.dll.ShamrockGetWavelengthLimits(self.dll.ShamrockGetGrating())
        if (wavelength < maxwl) and (wavelength > minwl):
            self.dll.ShamrockSetWavelength(wavelength)
            self._wl = self.dll.ShamrockGetCalibration(self._width)
        else:
            pass
        if wavelength < 10:
            self.dll.ShamrockGotoZeroOrder()
            time.sleep(0.3)
            self.dll.ShamrockGetCalibration(self._width)
            if not self.dll.ShamrockAtZeroOrder():
                print("ERROR: Did not reach zero order!")
        else:
            self.dll.ShamrockSetWavelength(wavelength)
            time.sleep(0.3)
            self._wl = self.dll.ShamrockGetCalibration(self._width)
            if (wavelength > maxwl) or (wavelength < minwl):
                print("You set the centre wavelength outside the usable range, wavelengths will be invalid")

    def get_input_port(self, input_port):
        pass

    def get_output_port(self, output_port):
        pass

    def get_input_slit_width(self, input_slit_width):
        pass

    def get_output_slit_width(self, output_slit_width):
        pass

    def get_delta_lambda(self, delta_lambda):
        pass

    def get_spectrometer_status(self, spectrometer_status):
        pass


############### end of functions necessary for L2Cspectro_interface ##########################

##############Shamrock wrapper################################################################
###sdk basic functions
    def shamrock_initialize(self):
        self.check(self.dll.ShamrockInitialize())
        return

    def shamrock_close(self):
        self.check(self.dll.ShamrockClose())
        return

    def shamrock_get_number_of_devices(self):
        number_of_devices = ct.c_int()
        self.check(self.dll.ShamrockNumberOfDevices(ct.byref(number_of_devices)))
        return number_of_devices.value

    def shamrock_get_function_return_description():
        """TODO"""
        return

###sdk eeprom functions
    def shamrock_get_serial_number(self):
        serial = ct.c_char()
        self.check(self.dll.ShamrockGetSerialNumber(self.deviceID, ct.byref(serial)))
        return serial.value













    def get_wavelength_limits(self):
        lambda_min = ct.c_float()
        lambda_max = ct.c_float()
        self.check(self.dll.ShamrockGetWavelengthLimits(self.deviceID, self.gratingID, ct.byref(lambda_min), ct.byref(lambda_max)))
        return (lambda_min.value, lambda_max.value)

    def get_number_of_gratings(self):
        ng = ct.c_int()
        self.check(self.dll.ShamrockGetNumberGratings(self.deviceID, ct.byref(ng)))
        return ng.value



    def get_detector_offset(self):
        det_offset = ct.c_float()
        self.check(self.dll.ShamrockGetDetectorOffset(self.deviceID, ct.byref(det_offset)))
        return det_offset.value

    def get_grating_offset(self):
        grating_offset = ct.c_int()
        self.check(self.dll.ShamrockGetGratingOffset(self.deviceID, self.gratingID, ct.byref(grating_offset)))
        return grating_offset.value

    def get_grating_info(self):
        lines = ct.c_float()
        blaze = ct.create_string_buffer(32)
        home = ct.c_int()
        offset = ct.c_int()
        self.check(self.dll.ShamrockGetGratingInfo(self.deviceID, self.gratingID, ct.byref(lines),\
                                                   ct.byref(blaze), ct.byref(home), ct.byref(offset)))
        return (lines.value, blaze.value, home.value, offset.value)

    def get_optical_parameters(self):
        focal_length = ct.c_float()
        ang_dev = ct.c_float()
        focal_tilt = ct.c_float()
        self.check(self.dll.ShamrockEepromGetOpticalParams(self.deviceID, ct.byref(focal_length), \
                                               ct.byref(ang_dev), ct.byref(focal_tilt)))
        return (focal_length.value, ang_dev.value, focal_tilt.value)


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

    def get_calibration(self):
        pixels_number = self.get_pixels_number()
        calibration_values = np.ones((pixel_number,), dtype=np.float)
        self.check(selfdellShamrockGetCalibration(self.deviceID, calibration_values.ct.data, pixels_number))
        return calibration_values

"""


    def Shutdown(self):
        self.andor.Shutdown()
        self.shamrock.Shutdown()
        self.closed = True

    def SetTemperature(self, temp):
        self.andor.SetTemperature(temp)

    def GetTemperature(self):
        return self.andor.GetTemperature()

    def GetSlitWidth(self):
        return self.shamrock.GetAutoSlitWidth(1)

    def GetGratingInfo(self):
        num_gratings = self.shamrock.GetNumberGratings()
        gratings = {}
        for i in range(num_gratings):
            lines, blaze, home, offset = self.shamrock.GetGratingInfo(i + 1)
            gratings[i + 1] = lines
        return gratings

    def GetGrating(self):
        return self.shamrock.GetGrating()

    def SetGrating(self, grating):
        status = self.shamrock.SetGrating(grating)
        self._wl = self.shamrock.GetCalibration(self._width)
        return status

    def SetDetectorOffset(self, offset):
        self.shamrock.SetDetectorOffset(offset)

    def GetDetectorOffset(self):
        return self.shamrock.GetDetectorOffset()

    def SetGratingOffset(self, offset):
        self.shamrock.SetGratingOffset(self.shamrock.GetGrating(), offset)

    def GetGratingOffset(self):
        return self.shamrock.GetGratingOffset(self.shamrock.GetGrating())

    def AbortAcquisition(self):
        self.andor.AbortAcquisition()

    def SetNumberAccumulations(self, number):
        self.andor.SetNumberAccumulations(number)

    def SetExposureTime(self, seconds):
        self.andor.SetExposureTime(seconds)
        self.exp_time = seconds

    def SetSlitWidth(self, slitwidth):
        self.shamrock.SetAutoSlitWidth(1, slitwidth)
        if self.mode is 'Image':
            self.andor.SetImage(1, 1, self.min_width, self.max_width, 1, self._height)
        else:
            self.CalcSingleTrackSlitPixels()
            self.andor.SetImage(1, 1, 1, self._width, self._hstart, self._hstop)

    def GetWavelength(self):
        return self._wl

    def SetFullImage(self):
        self.andor.SetImage(1, 1, 1, self._width, 1, self._height)
        self.mode = 'Image'

    def TakeFullImage(self):
        return self.TakeImage(self._width, self._height)

    def TakeImage(self, width, height):
        self.andor.StartAcquisition()
        acquiring = True
        while acquiring:
            status = self.andor.GetStatus()
            if status == 20073:
                acquiring = False
            elif not status == 20072:
                return None
        data = self.andor.GetAcquiredData(width, height)
        # return data.transpose()
        return data

    def SetCentreWavelength(self, wavelength):
        minwl, maxwl = self.shamrock.GetWavelengthLimits(self.shamrock.GetGrating())
        # if (wavelength < maxwl) and (wavelength > minwl):
        #     self.shamrock.SetWavelength(wavelength)
        #     self._wl = self.shamrock.GetCalibration(self._width)
        # else:
        #     pass
        if wavelength < 10:
            self.shamrock.GotoZeroOrder()
            time.sleep(0.3)
            self.shamrock.GetCalibration(self._width)
            if not self.shamrock.AtZeroOrder():
                print("ERROR: Did not reach zero order!")
        else:
            self.shamrock.SetWavelength(wavelength)
            time.sleep(0.3)
            self._wl = self.shamrock.GetCalibration(self._width)
            if (wavelength > maxwl) or (wavelength < minwl):
                print("You set the centre wavelength outside the usable range, wavelengths will be invalid")

    def CalcImageofSlitDim(self, extraborder=25):
        # Calculate which pixels in x direction are acutally illuminated (usually the slit will be much smaller than the ccd)
        visible_xpixels = (self.GetSlitWidth()) / self._pixelwidth
        min_width = round(self._width / 2 - visible_xpixels / 2)
        max_width = round(self._width / 2 + visible_xpixels / 2)

        # This two values have to be adapted if to fit the image of the slit on your detector !
        min_width -= extraborder  # 45#25
        max_width += extraborder  # 0#5

        if min_width < 1:
            min_width = 1
        if max_width > self._width:
            max_width = self._width

        print("Pixels for Image of Slit:" + str(min_width) + ' - ' + str(max_width))
        return min_width, max_width

    def SetImageofSlit(self):
        self.shamrock.SetWavelength(0)

        min_width, max_width = self.CalcImageofSlitDim()
        self.min_width = min_width
        self.max_width = max_width

        self.andor.SetImage(1, 1, self.min_width, self.max_width, 1, self._height)
        self.mode = 'Image'

    def TakeImageofSlit(self):
        return self.TakeImage(self.max_width - self.min_width + 1, self._height)

    def SetSingleTrackMinimumVerticalPixels(self, pixels):
        self.single_track_minimum_vertical_pixels = pixels

    def CalcSingleTrackSlitPixels(self):
        slitwidth = self.shamrock.GetAutoSlitWidth(1)
        pixels = (slitwidth / self._pixelheight)
        if pixels < self.single_track_minimum_vertical_pixels:  # read out a minimum of 7 pixels, this is the smallest height that could be seen on the detector, smaller values will give wrong spectra due to chromatic abberation
            pixels = self.single_track_minimum_vertical_pixels
        middle = round(self._height / 2)
        self._hstart = round(middle - pixels / 2)
        self._hstop = round(middle + pixels / 2) + 3
        print('Detector readout:' + str(self._hstart) + ' - ' + str(self._hstop - 3) + ' pixels, middle at ' + str(
            middle) + ', throwing away ' + str(self._hstop - 3) + '-' + str(self._hstop))
        # the -3 is a workaround as the detector tends to saturate the first two rows, so we take these but disregard them later

    def SetSingleTrack(self, hstart=None, hstop=None):
        if (hstart is None) or (hstop is None):
            self.CalcSingleTrackSlitPixels()
        else:
            self._hstart = hstart
            self._hstop = hstop
        self.andor.SetImage(1, 1, 1, self._width, self._hstart, self._hstop)
        self.mode = 'SingleTrack'

    def TakeSingleTrack(self):
        self.andor.StartAcquisition()
        acquiring = True
        while acquiring:
            status = self.andor.GetStatus()
            if status == 20073:
                acquiring = False
            elif not status == 20072:
                print(Andor.ERROR_CODE[status])
                return np.zeros((self._width, 7))
        data = self.andor.GetAcquiredData(self._width, (self._hstop - self._hstart) + 1)
        # data = np.mean(data, 1)
        data = data[:, 3:]  # throw away 'bad rows', see CalcSingleTrackSlitPixels(self) for details
        print('Acquired Data: ' + str(data.shape))
        # return data[:, 3:]  # throw away 'bad rows', see CalcSingleTrackSlitPixels(self) for details


return data
"""