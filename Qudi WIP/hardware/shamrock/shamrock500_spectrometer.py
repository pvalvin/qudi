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
from interface.spectrometer_interface import SpectrometerInterface
from core.util.modules import get_main_dir
import os

import numpy as np

import ctypes as ct
import time

class Shamrock(Base,SpectrometerInterface):

    _dll_location = ConfigOption('dll_location',missing='error')

    def recordSpectrum(self):
        pass

    def setExposure(self, exposureTime):
        pass

    def getExposure(self):
        pass

    ####################################################################################################################
    #           Basic Functions
    ####################################################################################################################
    def on_activate(self):
        """ Activate hardware module.
        """

        self.dll = ct.cdll.LoadLibrary(_dll_location)
        self.initialize()


    def initialize(path):
        self.dll.initialize(path)

    def on_deactivate():
        self.dll.close()

    def close():

    def get_number_devices(nodevices):

    def get_function_return_description(error,description,MaxDescStrLen):

    ####################################################################################################################
    #           EEPROM Functions
    ####################################################################################################################

    def get_serial_number(device,serial):

    def set_optical_params(device,FocalLength,AngularDaviation,FocalTilt):

    def get_optical_params(device,FocalLength,AngularDaviation,FocalTilt):

    ####################################################################################################################
    #           Gratings Functions
    ####################################################################################################################

    def set_grating(device,grating):

    def get_grating(device,grating):

    def wavelength_reset(device):

    def get_number_gratings(device,noGratings):

    def get_grating_info(device,Grating, Lines, Blaze, Home, Offset):

    def set_detector_offset(device,offset):

    def get_detector_offset(device,offset):

    def set_detector_offset_port2(device,offset):

    def get_detector_offset_port2(device,offset):

    def set_detector_offset_ex(device,offset):

    def get_detector_offset_ex(device,offset):

    def set_grating_offset(device,offset):

    def get_grating_offset(device,offset):

    def grating_is_present(device, present):

    def set_turret(device, Turret):

    def get_turret(device, Turret):

    ####################################################################################################################
    #           Wavelength Functions
    ####################################################################################################################

    def det_wavelength(device,wavelength):

    def get_wavelength(device, wavelength):
    def goto_zero_order(device):
    def at_zero_order(device,atZeroOrder):
    def get_wavelength_limits(device, Grating, Min, Max):
    def wavelength_is_present(device, present):

    ####################################################################################################################
    #           Slits Functions
    ####################################################################################################################
    def set_auto_slit_width(device, index, width):
    def get_auto_slit_width(device, index, width):
    def auto_slit_reset(device, index):
    def auto_slit_is_present(device, index, present):
    def set_auto_slit_coefficients(device, index, x1, y1, x2, y2):
    def get_auto_slit_coefficients(device, index, x1, y1, x2, y2):
    def set_slit_zero_position(device, index, offset):
    def get_slit_zero_position(device, index, offset):

    ####################################################################################################################
    #           Shutter Functions
    ####################################################################################################################

    def set_shutter(device, mode):
    def get_shutter(device, mode):
    def is_mode_possible(device, mode, possible):
    def shutter_is_present(device, present):

    ####################################################################################################################
    #           Filter Functions
    ####################################################################################################################

    def set_filter(device, filter):
    def get_filter(device, filter):
    def set_filter_info(device, Filter, Info):
    def get_filter_info(device, Filter, Info):
    def filter_reset(device):
    def filter_is_present(device, present):

    // sdkflipper
    functions

    ####################################################################################################################
    #           Flipper Functions
    ####################################################################################################################

    def set_flipper_mirror(device, flipper, port):
    def get_flipper_mirror(device, flipper, port):
    def flipper_mirror_reset(device, flipper):
    def flipper_mirror_is_present(device, flipper, present):
    def get_CCD_limits(device, port, Low, High):
    def set_flipper_mirror_position(device, flipper, position):
    def get_flipper_mirror_position(device, flipper, position):
    def set_flipper_mirror_max_position(device, flipper, max):

    ####################################################################################################################
    #           Accessory Functions
    ####################################################################################################################

    def set_accessory(device, Accessory, State):
    def get_accessory_state(device, Accessory, state):
    def accessory_is_present(device, present):

    ####################################################################################################################
    #           Focus Mirror Functions
    ####################################################################################################################

    def set_focus_mirror(device, focus):
    def get_focus_mirror(device, focus):
    def set_focus_mirror_max_steps(device, steps):
    def focus_mirror_reset(device):
    def focus_mirror_is_present(device, present):

    ####################################################################################################################
    #           Calibration Functions
    ####################################################################################################################

    def set_pixel_width(device, Width):
    def set_number_pixels(device, NumberPixels):
    def get_pixel_width(device, Width):
    def get_number_pixels(device, NumberPixels):
    def get_calibration(device, CalibrationValues, NumberPixels):
    def get_pixel_calibration_coefficients(device, A, B, C, D):

    ####################################################################################################################
    #           Iris Functions
    ####################################################################################################################

    def iris_is_present(device, iris, present):
    def set_iris(device, iris, value):
    def get_iris(device, iris, value):
    ####################################################################################################################
    #           Focus mirror tilt Functions
    ####################################################################################################################

    def focus_mirror_tilt_is_present(device, present):
    def set_focus_mirror_tilt(device, tilt):
    def get_focus_mirror_tilt(device, tilt):
    def set_focus_mirror_tilt_offset(device, entrancePort, exitPort, offset):
    def get_focus_mirror_tilt_offset(device, entrancePort, exitPort, offset):
    def move_turret_to_safe_change_position(device):
















