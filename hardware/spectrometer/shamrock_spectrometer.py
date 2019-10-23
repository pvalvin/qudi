# -*- coding: utf-8 -*-


from core.module import Base
from interface.spectrometer_interface import SpectrometerInterface
from core.util.modules import get_main_dir
import os

import numpy as np

import ctypes as ct
import time

class Shamrock(Base, SpectrometerInterface):

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
        """ Deactivate module.
        """
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
        """
        Returns the current grating identification (1 to 3)
        Tested : yes
        """
        grating = ct.c_int()
        self.check(self.dll.ShamrockGetGrating(self.deviceID, ct.byref(grating)))
        return grating.value-1

    def get_central_wavelength(self):
        lambda0 = ct.c_float()
        self.check(self.dll.ShamrockGetWavelength(self.deviceID, ct.byref(lambda0)))
        return lambda0.value

    def get_input_port(self):
        """
        Returns the current port for the specified flipper mirror.
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
        Returns the current port for the specified flipper mirror.
        Tested : yes
        """
        output_port = ct.c_int()
        if self.shamrock_flipper_mirror_is_present(2)==1:
            self.check(self.dll.ShamrockGetFlipperMirror(self.deviceID, 2, ct.byref(output_port)))
            return output_port.value
        else:
            return 0

    def get_input_slit_width(self):
        """
        Returns the input slit width (um) in case of a motorized slit, -1 instead
        tested : yes
        """
        input_slit_width = ct.c_float()
        if self.get_input_port()==1:
            slit_index=1
        else:
            slit_index=2

        if self.shamrock_auto_slit_is_present(slit_index)==1:
            self.check(self.dll.ShamrockGetAutoSlitWidth(self.deviceID, slit_index, ct.byref(input_slit_width)))
            return input_slit_width.value
        else:
            return -1

    def get_output_slit_width(self):
        """
        Returns the output slit width (um) in case of a motorized slit, -1 instead
        tested : yes
        """
        output_slit_width = ct.c_float()
        if self.get_output_port()==1:
            slit_index=3
        else:
            slit_index=4

        if self.shamrock_auto_slit_is_present(slit_index)==1:
            self.check(self.dll.ShamrockGetAutoSlitWidth(self.deviceID, slit_index, ct.byref(output_slit_width)))
            return output_slit_width.value
        else:
            return -1

    def get_delta_lambda(self):
        pass

    def get_spectrometer_status(self):
        return self.spectrometer_status

    def set_grating(self, grating):
        """
        Sets the required grating

        @param int grating: grating identification number
        @return: void
        """
        self.check(self.dll.ShamrockSetGrating(self.deviceID, grating))
        return

    def set_central_wavelength(self, wavelength):
        self.check(self.dll.ShamrockSetWavelength(self.deviceID, wavelength))
        return


############### end of functions necessary for L2Cspectro_interface ##########################

# ------------------------------------------------------------------------------------------##
#                                 Shamrock wrapper                                          ##
# ------------------------------------------------------------------------------------------##


# sdk basic functions
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

    def shamrock_flipper_mirror_is_present(self, flipper):
        present = ct.c_int()
        self.check(self.dll.ShamrockFlipperMirrorIsPresent(self.deviceID, flipper, ct.byref(present)))
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


    def getExposure(self):
        pass

    def recordSpectrum(self):
        pass

    def setExposure(self):
        pass
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