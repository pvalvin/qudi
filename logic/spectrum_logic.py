# -*- coding: utf-8 -*-
"""
This file contains the Qudi logic class that captures and processes photoluminescence
spectra and the spot image.

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
from enum import Enum

from core.connector import Connector
from core.statusvariable import StatusVar
from core.util.mutex import Mutex
from core.util.network import netobtain
from logic.generic_logic import GenericLogic
from core.configoption import ConfigOption

from interface.grating_spectrometer_interface import PortType
from interface.science_camera_interface import ReadMode, ShutterState
from hardware.camera.andor_camera import TriggerMode

from scipy import optimize

import time


class AcquisitionMode(Enum):
    """ Internal class defining the possible read modes of the camera

    SINGLE_SCAN : single scan acquisition
    MULTI_SCAN : multiple scan acquisition
    LIVE_SCAN : live scan acquisition
    """
    SINGLE_SCAN = 0
    MULTI_SCAN = 1
    LIVE_SCAN = 2


class SpectrumLogic(GenericLogic):
    """ This logic module handle the spectrometer gratings and camera """

    # declare connectors
    spectrometer = Connector(interface='GratingSpectrometerInterface')
    camera = Connector(interface='ScienceCameraInterface')
    savelogic = Connector(interface='SaveLogic')

    # declare status variables (logic attribute) :
    _reverse_data_with_side_output = ConfigOption('reverse_data_with_side_output', False)

    # declare status variables (logic attribute) :
    _acquired_data = StatusVar('wavelength_calibration', np.empty((2, 0)))
    _wavelength_calibration = StatusVar('wavelength_calibration', 0)
    _dispersion_fitting_parameters = StatusVar('dispersion_fitting_parameters', None)

    # declare status variables (camera attribute) :
    _camera_gain = StatusVar('camera_gain', None)
    _readout_speed = StatusVar('readout_speed', None)
    _exposure_time = StatusVar('exposure_time', None)
    _scan_delay = StatusVar('scan_delay', 0)
    _number_of_scan = StatusVar('number_of_scan', 1)
    _acquisition_mode = StatusVar('acquisition_mode', 'SINGLE_SCAN')
    _temperature_setpoint = StatusVar('temperature_setpoint', None)

    # cosmic rejection coeff :
    _coeff_rej_cosmic = StatusVar('coeff_cosmic_rejection', 2.2)

    _sigStart = QtCore.Signal()
    _sigCheckStatus = QtCore.Signal()
    ##############################################################################
    #                            Basic functions
    ##############################################################################

    def __init__(self, **kwargs):
        """ Create SpectrumLogic object with connectors and status variables loaded.

          @param dict kwargs: optional parameters
        """
        super().__init__(**kwargs)
        self.threadlock = Mutex()

        # Public attributes
        self.spectro_constraints = None
        self.camera_constraints = None

        # Private attributes
        self._grating_index = None
        self._center_wavelength = None
        self._input_ports = None
        self._output_ports = None
        self._input_port = None
        self._output_port = None
        self._input_slit_width = None
        self._output_slit_width = None
        self._read_mode = None
        self._trigger_mode = None
        self._active_tracks = None
        self._image_advanced = None
        self._shutter_state = None
        self._loop_counter = None
        self._loop_timer = None

    def on_activate(self):
        """ Initialisation performed during activation of the module. """

        self.spectro_constraints = self.spectrometer().get_constraints()
        self.camera_constraints = self.camera().get_constraints()

        ports = self.spectro_constraints.ports
        self._output_ports = [port for port in ports if port.type == PortType.OUTPUT_SIDE or
                              port.type == PortType.OUTPUT_FRONT]
        self._input_ports = [port for port in ports if port.type == PortType.INPUT_SIDE or
                             port.type == PortType.INPUT_FRONT]

        # Get current physical state
        self._grating_index = self.spectrometer().get_grating_index()
        self._center_wavelength = self.spectrometer().get_wavelength()
        self._input_port = self.spectrometer().get_input_port()
        self._output_port = self.spectrometer().get_output_port()
        self._input_slit_width = [self.spectrometer().get_slit_width(port.type) if port.is_motorized else None
                                  for port in self._input_ports]
        self._output_slit_width = [self.spectrometer().get_slit_width(port.type) if port.is_motorized else None
                                   for port in self._output_ports]

        # Get camera state
        self._read_mode = self.camera().get_read_mode()
        self._trigger_mode = self.camera().get_trigger_mode()

        # Try status variable value or take current hardware value if status variable is None
        self.readout_speed = self._readout_speed or self.camera().get_readout_speed()
        self.camera_gain = self._camera_gain or self.camera().get_gain()
        self.exposure_time = self._exposure_time or self.camera().get_exposure_time()

        self.fit_spectrometer_dispersion()

        if self.camera_constraints.has_cooler:
            self.temperature_setpoint = self._temperature_setpoint or self.camera().get_temperature_setpoint()

        self._image_advanced = self.camera().get_image_advanced_parameters()

        if self._active_tracks == None:
            self._active_tracks = self.camera().get_active_tracks()

        if self.camera_constraints.has_shutter:
            self._shutter_state = self.camera().get_shutter_state()

        # QTimer for asynchronous execution :
        self._loop_counter = 0

        self._acquisition_params = OrderedDict()

        self._sigStart.connect(self._start_acquisition)
        self._sigCheckStatus.connect(self._check_status, QtCore.Qt.QueuedConnection)
        self._loop_timer = QtCore.QTimer()
        self._loop_timer.setSingleShot(True)
        self._loop_timer.timeout.connect(self._acquisition_loop)

    def on_deactivate(self):
        """ Deinitialisation performed during deactivation of the module. """
        if self.module_state() != 'idle':
            self.stop_acquisition()
            self.log.warning('Stopping running acquisition du to module deactivation.')

        self._sigStart.disconnect()
        self._sigCheckStatus.disconnect()

    ##############################################################################
    #                            Acquisition functions
    ##############################################################################

    def take_acquisition(self):
        """ Method use by other modules and script to start acquisition, wait for the end and return the result

        @return (np.ndarray):  The newly acquired data

        """
        if self.module_state() == 'locked':
            self.log.error("Module acquisition is still running, module state is currently locked.")
        self.start_acquisition()
        while self.module_state() != 'idle':
            time.sleep(0.1)
        return self._acquired_data

    def start_acquisition(self):
        """ Start acquisition in the module's thread and return immediately """
        if self.module_state() == 'locked':
            self.log.error("Module acquisition is still running, module state is currently locked.")
            return
        self.module_state.lock()
        self._sigStart.emit()

    def _start_acquisition(self):
        """ Start acquisition method initializing the acquisitions constants and calling the acquisition method
        """

        self._acquired_data = []
        if self._acquisition_mode == 'MULTI_SCAN':
            self._loop_counter = self._number_of_scan
        self._acquisition_loop()

    def get_ready_state(self):
        """ Getter method returning if the camera hardware is acquiring or not

        @return: (bool) camera hardware idle ?
        """
        return self.camera().get_ready_state()

    def _acquisition_loop(self):
        """ Acquisition method starting hardware acquisition and emitting Qtimer signal connected to check status method
        """
        self._loop_counter -= 1
        self.camera().start_acquisition()
        self._sigCheckStatus.emit()

    def _check_status(self):
        """ Method / Slot used by the acquisition call by Qtimer signal to check if the acquisition is complete """
        # If module unlocked by stop_acquisition
        if self.module_state() != 'locked':
            self._acquired_data = self.get_acquired_data()
            #self._update_acquisition_params()
            self.log.debug("Acquisition stopped. Status loop stopped.")
            return

        # If hardware still running
        if not self.get_ready_state():
            self._sigCheckStatus.emit()
            return

        # Acquisition is finished
        if self._acquisition_mode == 'SINGLE_SCAN':
            self._acquired_data = self.get_acquired_data()
            #self._update_acquisition_params()
            self.module_state.unlock()
            self.log.debug("Acquisition finished : module state is 'idle' ")
            return

        elif self._acquisition_mode == 'LIVE_SCAN':
            self._loop_counter += 1
            self._acquired_data = self.get_acquired_data()
            self._acquisition()
            return

        else:
            self._acquired_data.append(self.get_acquired_data())

            if self._loop_counter <= 0:
                #self._update_acquisition_params()
                self.module_state.unlock()
                self.log.debug("Acquisition finished : module state is 'idle' ")
            else:
                self._loop_timer.start(self.scan_delay*1000)
                return

    def reject_cosmic(self, data):
        """ This function is used to reject cosmic features from acquired spectrum

        It is done by computing the standard deviation of an ensemble of accumulated scan.
        The rejection is carry out with a mask rejecting values outside their standard deviation on each pixel
        """
        mean_data = np.nanstd(data, axis=0)
        std_dev_data = np.nanstd((data-mean_data)**2, axis=0)
        mask_min = mean_data - std_dev_data * self._coeff_rej_cosmic
        mask_max = mean_data + std_dev_data * self._coeff_rej_cosmic
        if len(data.shape) == 2:
            clean_data = np.ma.masked_array([np.ma.masked_outside(pixel, mask_min[i], mask_max[i])
                                             for i,pixel in enumerate(data.T)]).T
            return clean_data
        clean_data = np.transpose(np.empty(np.shape(data)), (1, 2, 0))
        for i,track in enumerate(np.transpose(data, (1, 2, 0))):
            clean_track = np.ma.masked_array([np.ma.masked_outside(pixel, mask_min[i, j], mask_max[i, j])
                                             for j,pixel in enumerate(track)])
            clean_data = np.append(clean_data, clean_track)
        return np.transpose(clean_data,(2,0,1))

    def stop_acquisition(self):
        """ Method to abort the acquisition """
        self.module_state.unlock()
        self.camera().abort_acquisition()
        self.log.debug("Acquisition stopped : module state is 'idle' ")

    @property
    def acquired_data(self):
        """ Getter method returning the last acquired data. """
        return self._acquired_data

    @property
    def acquisition_params(self):
        """ Getter method returning the last acquisition parameters. """
        return self._acquisition_params

    def _update_acquisition_params(self):
        """ Getter method returning the last acquisition parameters. """
        self._acquisition_params['read_mode'] = self.read_mode
        if self.read_mode == 'IMAGE_ADVANCED':
            self._acquisition_params['image_advanced'] = (self.image_advanced_binning, self.image_advanced_area)
        if self.read_mode == 'MULTIPLE_TRACKS':
            self._acquisition_params['multiple_tracks'] = self.active_tracks
        self._acquisition_params['camera_gain'] = self.camera_gain
        self._acquisition_params['readout_speed (Hz)'] = self.readout_speed
        self._acquisition_params['exposure_time (s)'] = self.exposure_time
        self._acquisition_params['scan_delay (s)'] = self.scan_delay
        self._acquisition_params['number_of_scan'] = self.number_of_scan
        self._acquisition_params['center_wavelength  (m)'] = self.center_wavelength
        self._acquisition_params['grating_index'] = self.grating_index
        self._acquisition_params['spectro_ports'] = self.input_port, self.output_port
        self._acquisition_params['slit_width (m)'] = self._input_slit_width, self._output_slit_width
        self._acquisition_params['wavelength_calibration (m)'] = self.wavelength_calibration

    def save_acquired_data(self, filename=None):

        filepath = self.savelogic().get_path_for_module(module_name='spectrum_logic')

        self.savelogic().save_data(self._acquired_data, filepath=filepath,
                                   parameters=self.acquisition_params,filename=filename)

    ##############################################################################
    #                            Spectrometer functions
    ##############################################################################
    # All functions defined in this part should be used to
    #
    #
    ##############################################################################
    #                            Gratings functions
    ##############################################################################

    @property
    def grating_index(self):
        """ Getter method returning the grating index used by the spectrometer.

        @return (int): active grating index
        """
        return self._grating_index

    @grating_index.setter
    def grating_index(self, grating_index):
        """ Setter method setting the grating index to use by the spectrometer.

        @param (int) grating_index: gating index to set active
        """
        if self.module_state() == 'locked':
            self.log.error("Acquisition process is currently running : you can't change this parameter"
                           " until the acquisition is completely stopped ")
            return
        grating_index = int(grating_index)
        if grating_index == self._grating_index:
            return
        number_of_gratings = len(self.spectro_constraints.gratings)
        if not 0 <= grating_index < number_of_gratings:
            self.log.error('Grating number parameter is not correct : it must be in range 0 to {} '
                           .format(number_of_gratings - 1))
            return
        self.spectrometer().set_grating_index(grating_index)
        self._grating_index = self.spectrometer().get_grating_index()

    ##############################################################################
    #                            Wavelength functions
    ##############################################################################

    @property
    def center_wavelength(self):
        """Getter method returning the center wavelength of the measured spectral range.

        @return: (float) the spectrum center wavelength

        Tested : yes
        SI check : yes
        """
        return self._center_wavelength + self._wavelength_calibration

    @center_wavelength.setter
    def center_wavelength(self, wavelength):
        """Setter method setting the center wavelength of the measured spectral range.

        @param wavelength: (float) center wavelength


        Tested : yes
        SI check : yes
        """
        if self.module_state() == 'locked':
            self.log.error("Acquisition process is currently running : you can't change this parameter"
                           " until the acquisition is completely stopped ")
            return
        wavelength = float(wavelength)
        if wavelength != 0:
            wavelength = float(wavelength - self._wavelength_calibration)
        else:
            wavelength = float(wavelength)
        wavelength_max = self.spectro_constraints.gratings[self._grating_index].wavelength_max
        if not 0 <= wavelength < wavelength_max:
            self.log.error('Wavelength parameter is not correct : it must be in range {} to {} '
                           .format(0, wavelength_max))
            return
        self.spectrometer().set_wavelength(wavelength)
        self._center_wavelength = self.spectrometer().get_wavelength()

    def _fitting_correction(self, lam_c, pixels, a, b, c, d, e):
        """ Function both used by the fitting function and the wavelength spectrum. This polynomial function
        depending on both the pixels position and the center wavelength correct the analytic dispersion through
        the error with hardware dispersion function.

        @return fitting_correction: (list or ndarray) correction of the analytic dispersion
        """
        return (a * lam_c + b) * pixels ** 2 + (c * lam_c + d) * pixels + e

    def fit_spectrometer_dispersion(self):
        """ Method fitting the hardware wavelength dispersion with the polynomial fitting_correction function to update
        fitting parameters.

        """

        def _func(M, *args):
            x, y = M
            arr = np.zeros(x.shape)
            for i in range(len(args) // 5):
                arr += self._fitting_correction(x, y, *args[i * 5:i * 5 + 5])
            return arr

        image_width = self.camera_constraints.width
        pixel_width = self.camera_constraints.pixel_size_width

        diff_surf = self.spectrometer().get_spectrometer_dispersion(image_width, pixel_width) - self._analytic_dispersion()

        x = self.center_wavelength
        y = np.arange(-image_width//2, image_width//2 - image_width%2)*pixel_width
        X, Y = np.meshgrid(x, y)
        xdata = np.vstack((X.ravel(), Y.ravel()))
        ydata = diff_surf.T.ravel()

        popt, pcov = optimize.curve_fit(_func, xdata, ydata, p0=[0, 0, 0, 0, 0])
        self._dispersion_fitting_parameters = popt


    def _analytic_dispersion(self):
        """ Analytic dispersion calculation based on hardware constraints parameters and the actual center wavelength
        based on geometric optics for a standard Czerny-Turner spectrometer configuration.

        @return: (ndarray) analytic wavelength array
        """

        image_width = self.camera_constraints.width
        pixel_width = self.camera_constraints.pixel_size_width
        focal_length = self.spectro_constraints.focal_length
        angular_dev = self.spectro_constraints.angular_deviation
        focal_tilt = self.spectro_constraints.focal_tilt
        grating = self.spectro_constraints.gratings[self.grating_index]
        lam_c = self.center_wavelength

        trans_eq = lambda alpha: (np.sin(angular_dev + alpha) + np.sin(alpha - angular_dev)) - lam_c * grating.ruling

        alpha = optimize.newton(trans_eq, 0)

        pixels_vector = np.arange(-image_width // 2, image_width // 2 - image_width % 2) * pixel_width
        theta = np.arctan(pixels_vector * np.cos(focal_tilt) / focal_length)
        effective_rulling = grating.ruling / np.cos(angular_dev + alpha)

        return 1/effective_rulling*(np.sin(angular_dev+alpha+theta)-np.sin(angular_dev+alpha)) + lam_c

    @property
    def wavelength_spectrum(self):
        """Getter method returning the wavelength array of the full measured spectral range.
        (used for plotting spectrum with the spectral range)

        @return: (ndarray) measured wavelength array

        Tested : yes (need to
        SI check : yes
        """
        image_width = self.camera_constraints.width
        pixel_width = self.camera_constraints.pixel_size_width
        pixels_vector = np.arange(-image_width // 2, image_width // 2 - image_width % 2) * pixel_width
        fitting_correction = self._fitting_correction(self.center_wavelength, pixels_vector, *self._dispersion_fitting_parameters)
        #return self._analytic_dispersion() + fitting_correction
        return self.spectrometer().get_spectrometer_dispersion(image_width, pixel_width) + self.wavelength_calibration

    @property
    def wavelength_calibration(self):
        """Getter method returning the wavelength calibration parameter currently used for
        shifting the spectrum.

        @return: (float) wavelength_calibration used for spectrum calibration
        """
        return self._wavelength_calibration

    @wavelength_calibration.setter
    def wavelength_calibration(self, wavelength_calibration):
        """Setter method

        @param wavelength_calibration (float) : wavelength shift used for spectrum calibration

        """
        if self.module_state() == 'locked':
            self.log.error("Acquisition process is currently running : you can't change this parameter"
                           " until the acquisition is completely stopped ")
            return
        self._wavelength_calibration = wavelength_calibration


    ##############################################################################
    #                      Ports and Slits functions
    ##############################################################################

    @property
    def input_port(self):
        """Getter method returning the active current input port of the spectrometer.

        @return: (int) active input port (0 front and 1 side)

        Tested : yes
        SI check : yes
        """
        return self._input_port.name

    @input_port.setter
    def input_port(self, input_port):
        """Setter method setting the active current input port of the spectrometer.

        @param input_port: (str|PortType) active input port (front or side)


        Tested : yes
        SI check : yes
        """
        if self.module_state() == 'locked':
            self.log.error("Acquisition process is currently running : you can't change this parameter"
                           " until the acquisition is completely stopped ")
            return
        if len(self._input_ports) < 2:
            self.log.error('Input port has no flipper mirror : this port can\'t be changed ')
            return
        if isinstance(input_port, str) and input_port in PortType.__members__:
            input_port = PortType[input_port]
        if not np.any([input_port==port.type for port in self._input_ports]):
            self.log.error('Function parameter must be an INPUT value from the input ports of the camera ')
            return
        if input_port == self._input_port:
            return
        self.spectrometer().set_input_port(input_port)
        self._input_port = self.spectrometer().get_input_port()

    @property
    def output_port(self):
        """Getter method returning the active current output port of the spectrometer.

        @return: (int) active output port (0 front and 1 side)

        Tested : yes
        SI check : yes
        """
        return self._output_port.name

    @output_port.setter
    def output_port(self, output_port):
        """Setter method setting the active current output port of the spectrometer.

        @param output_port: (int) active output port (0 front and 1 side)


        Tested : yes
        SI check : yes
        """
        if self.module_state() == 'locked':
            self.log.error("Acquisition process is currently running : you can't change this parameter"
                           " until the acquisition is completely stopped ")
            return
        if len(self._output_ports) < 2:
            self.log.error('Output port has no flipper mirror : this port can\'t be changed ')
            return
        if isinstance(output_port, str) and output_port in PortType.__members__:
            output_port = PortType[output_port]
        if not np.any([output_port==port.type for port in self._output_ports]):
            self.log.error('Function parameter must be an OUTPUT value from the output ports of the camera ')
            return
        if output_port == self._output_port:
            return
        self.spectrometer().set_output_port(output_port)
        self._output_port = self.spectrometer().get_output_port()

    @property
    def input_slit_width(self):
        """Getter method returning the active input port slit width of the spectrometer.

        @return: (float) input port slit width
        """
        return self.get_input_slit_width()

    @input_slit_width.setter
    def input_slit_width(self, slit_width):
        """Setter method setting the active input port slit width of the spectrometer.

        @param slit_width: (float) input port slit width

        """
        self.set_input_slit_width(slit_width)

    @property
    def output_slit_width(self):
        """Getter method returning the active output port slit width of the spectrometer.

        @return: (float) output port slit width

        Tested : yes
        SI check : yes
        """
        return self.get_output_slit_width()

    @output_slit_width.setter
    def output_slit_width(self, slit_width):
        """Setter method setting the active output port slit width of the spectrometer.

        @param slit_width: (float) output port slit width

        Tested : yes
        SI check : yes
        """
        self.set_output_slit_width(slit_width)

    def get_input_slit_width(self, port='current'):
        """Getter method returning the active input port slit width of the spectrometer.

        @param input port: (Port|str) port
        @return: (float) input port slit width
        """
        if isinstance(port, PortType):
            port = port.name
        port = str(port)
        if port == 'current':
            port = self._input_port
        elif port == 'front':
            port = PortType.INPUT_FRONT
        elif port == 'side':
            port = PortType.INPUT_SIDE
        else:
            self.log.error("Port parameter do not match with the possible values : 'current', 'front' and 'side' ")
            return
        input_types = [port.type for port in self._input_ports]
        if port not in input_types:
            self.log.error('Input port {} doesn\'t exist on your hardware '.format(port.name))
            return
        index = input_types.index(port)
        return self._input_slit_width[index]

    def set_input_slit_width(self, slit_width, port='current'):
        """Setter method setting the active input port slit width of the spectrometer.

        @param slit_width: (float) input port slit width
        @param input port: (Port|str) port
        """
        if isinstance(port, PortType):
            port = port.name
        port = str(port)
        slit_width = float(slit_width)
        if port == 'current':
            port = self._input_port
        elif port == 'front':
            port = PortType.INPUT_FRONT
        elif port == 'side':
            port = PortType.INPUT_SIDE
        else:
            self.log.error("Port parameter do not match with the possible values : 'current', 'front' and 'side' ")
            return
        input_types = [port.type for port in self._input_ports]
        if port not in input_types:
            self.log.error('Input port {} doesn\'t exist on your hardware '.format(port.name))
            return
        index = input_types.index(port)
        if self._input_slit_width[index] == slit_width:
            return
        self.spectrometer().set_slit_width(port, slit_width)
        self._input_slit_width[index] = self.spectrometer().get_slit_width(port)

    def get_output_slit_width(self, port='current'):
        """Getter method returning the active output port slit width of the spectrometer.

        @param output port: (Port|str) port
        @return: (float) output port slit width

        Tested : yes
        SI check : yes
        """
        port = str(port)
        if port == 'current':
            port = self._output_port
        elif port == 'front':
            port = PortType.OUTPUT_FRONT
        elif port == 'side':
            port = PortType.OUTPUT_SIDE
        else:
            self.log.error("Port parameter do not match with the possible values : 'current', 'front' and 'side' ")
            return
        output_types = [port.type for port in self._output_ports]
        if port not in output_types:
            self.log.error('Output port {} doesn\'t exist on your hardware '.format(port.name))
            return
        index = output_types.index(port)
        return self._output_slit_width[index]

    def set_output_slit_width(self, slit_width, port='current'):
        """Setter method setting the active output port slit width of the spectrometer.

        @param slit_width: (float) output port slit width
        @param output port: (Port|str) port

        Tested : yes
        SI check : yes
        """
        if isinstance(port, PortType):
            port = port.name
        port = str(port)
        slit_width = float(slit_width)
        if port == 'current':
            port = self._output_port
        elif port == 'front':
            port = PortType.OUTPUT_FRONT
        elif port == 'side':
            port = PortType.OUTPUT_SIDE
        else:
            self.log.error("Port parameter do not match with the possible values : 'current', 'front' and 'side' ")
            return
        output_types = [port.type for port in self._output_ports]
        if port not in output_types:
            self.log.error('Output port {} doesn\'t exist on your hardware '.format(port.name))
            return
        index = output_types.index(port)
        if self._output_slit_width[index] == slit_width:
            return
        self.spectrometer().set_slit_width(port, slit_width)
        self._output_slit_width[index] = self.spectrometer().get_slit_width(port)

    ##############################################################################
    #                            Camera functions
    ##############################################################################
    # All functions defined in this part should be used to
    #
    #
    ##############################################################################
    #                           Basic functions
    ##############################################################################

    def get_acquired_data(self):
        """ Return an array of last acquired data.

           @return: Data in the format depending on the read mode.

           Depending on the read mode, the format is :
           'FVB' : 1d array
           'MULTIPLE_TRACKS' : list of 1d arrays
           'IMAGE' 2d array of shape (width, height)
           'IMAGE_ADVANCED' 2d array of shape (width, height)

           Each value might be a float or an integer.
           """
        if self._reverse_data_with_side_output and self.output_port == "OUTPUT_SIDE":
            return netobtain(self.camera().get_acquired_data()[:, ::-1])
        return netobtain(self.camera().get_acquired_data())

    ##############################################################################
    #                           Read mode functions
    ##############################################################################

    @property
    def read_mode(self):
        """Getter method returning the current read mode used by the camera.

        @return: (str) read mode logic attribute

        Tested : yes
        SI check : yes
        """
        return self._read_mode

    @read_mode.setter
    def read_mode(self, read_mode):
        """Setter method setting the read mode used by the camera.

        @param read_mode: (str|ReadMode) read mode

        """
        if self.module_state() == 'locked':
            self.log.error("Acquisition process is currently running : you can't change this parameter"
                           " until the acquisition is completely stopped ")
            return
        if read_mode == self._read_mode:
            return
        if isinstance(read_mode, str) and read_mode in ReadMode.__members__:
            read_mode = ReadMode[read_mode]
        if read_mode not in self.camera_constraints.read_modes:
            self.log.error("Read mode parameter do not match with any of the available read "
                           "modes of the camera ")
            return
        self.camera().set_read_mode(read_mode)
        self._read_mode = self.camera().get_read_mode().name

    @property
    def readout_speed(self):
        """Getter method returning the readout speed used by the camera.

        @return: (float) readout speed in Hz

        Tested : yes
        SI check : yes
        """
        return self._readout_speed

    @readout_speed.setter
    def readout_speed(self, readout_speed):
        """Setter method setting the readout speed to use by the camera.

        @param readout_speed: (float) readout speed in Hz


        Tested : yes
        SI check : yes
        """
        if self.module_state() == 'locked':
            self.log.error("Acquisition process is currently running : you can't change this parameter"
                           " until the acquisition is completely stopped ")
            return
        readout_speed = float(readout_speed)
        index = (np.abs(np.array(self.camera_constraints.readout_speeds)-readout_speed)).argmin()
        readout_speed = self.camera_constraints.readout_speeds[index]
        if readout_speed == self._readout_speed:
            return
        self.camera().set_readout_speed(readout_speed)
        self._readout_speed = self.camera().get_readout_speed()

    @property
    def active_tracks(self):
        """Getter method returning the read mode tracks parameters of the camera.

        @return: (list) active tracks positions [1st track start, 1st track end, ... ]

        Tested : yes
        SI check : yes
        """
        return self._active_tracks

    @active_tracks.setter
    def active_tracks(self, active_tracks):
        """
        Setter method setting the read mode tracks parameters of the camera.

        @param active_tracks: (list) active tracks positions [1st track start, 1st track end, ... ]


        Tested : yes
        SI check : yes
        """
        if self.module_state() == 'locked':
            self.log.error("Acquisition process is currently running : you can't change this parameter"
                           " until the acquisition is completely stopped ")
            return
        active_tracks = np.array(active_tracks, dtype=int)
        image_height = self.camera_constraints.height
        if not (np.all(0<=active_tracks) and np.all(active_tracks<image_height)):
            self.log.error("Active tracks positions are out of range : some position given are outside the "
                             "camera width in pixel ")
            return
        if not len(active_tracks)%2 == 0:
            active_tracks = np.append(active_tracks, image_height-1)
        active_tracks = [(active_tracks[i], active_tracks[i+1]) for i in range(0, len(active_tracks), 2)]
        self.camera().set_active_tracks(active_tracks)
        self._active_tracks = self.camera().get_active_tracks()

    @property
    def image_advanced_binning(self):
        return {'horizontal_binning': self._image_advanced.horizontal_binning,
                 'vertical_binning': self._image_advanced.vertical_binning}

    @image_advanced_binning.setter
    def image_advanced_binning(self, binning):
        if self.module_state() == 'locked':
            self.log.error("Acquisition process is currently running : you can't change this parameter"
                           " until the acquisition is completely stopped ")
            return
        binning = list(binning)
        if len(binning) != 2:
            self.log.error("Binning parameter must be a tuple or list of 2 elements respectively the horizontal and "
                           "vertical binning ")
            return
        width = self.camera_constraints.width
        height = self.camera_constraints.height
        if not 0<binning[0]<width or not 0<binning[1]<height:
            self.log.error("Binning parameter is out of range : the binning is outside the camera dimensions in pixel ")
            return
        self._image_advanced.horizontal_binning = int(binning[0])
        self._image_advanced.vertical_binning = int(binning[1])

        self.camera().set_image_advanced_parameters(self._image_advanced)

    @property
    def image_advanced_area(self):
        return {'horizontal_range': (self._image_advanced.horizontal_start, self._image_advanced.horizontal_end),
                'vertical_range': (self._image_advanced.vertical_start, self._image_advanced.vertical_end)}

    @image_advanced_area.setter
    def image_advanced_area(self, image_advanced_area):
        if self.module_state() == 'locked':
            self.log.error("Acquisition process is currently running : you can't change this parameter"
                           " until the acquisition is completely stopped ")
            return
        image_advanced_area = list(image_advanced_area)
        if len(image_advanced_area) != 4:
            self.log.error("Image area parameter must be a tuple or list of 4 elements like this [horizontal start, "
                           "horizontal end, vertical start, vertical end] ")
            return
        width = self.camera_constraints.width
        height = self.camera_constraints.height
        if not (0 <= image_advanced_area[0] < image_advanced_area[1] < width):
            self.log.error("Image area horizontal parameter are out of range : "
                           "the limits are outside the camera dimensions in pixel or not sorted ")
            return
        if not (0 <= image_advanced_area[2] < image_advanced_area[3] < height):
            self.log.error("Image area vertical parameter are out of range : "
                           "the limits are outside the camera dimensions in pixel or not sorted")
            return
        hbin = self._image_advanced.horizontal_binning
        vbin = self._image_advanced.vertical_binning
        if not (image_advanced_area[1]-image_advanced_area[0]+1)%hbin==0:
            image_advanced_area[1] = (image_advanced_area[1] - image_advanced_area[0] + 1) // hbin * hbin + image_advanced_area[0]
        if not (image_advanced_area[3]-image_advanced_area[2]+1)%vbin==0:
            image_advanced_area[3] = (image_advanced_area[3] - image_advanced_area[2] + 1) // vbin * vbin + image_advanced_area[2]
        self._image_advanced.horizontal_start = int(image_advanced_area[0])
        self._image_advanced.horizontal_end = int(image_advanced_area[1])
        self._image_advanced.vertical_start = int(image_advanced_area[2])
        self._image_advanced.vertical_end = int(image_advanced_area[3])

        self.camera().set_image_advanced_parameters(self._image_advanced)

    ##############################################################################
    #                           Acquisition functions
    ##############################################################################

    @property
    def acquisition_mode(self):
        """Getter method returning the current acquisition mode used by the logic module during acquisition.

        @return (str): acquisition mode

        Tested : yes
        SI check : yes
        """
        return self._acquisition_mode


    @acquisition_mode.setter
    def acquisition_mode(self, acquisition_mode):
        """Setter method setting the acquisition mode used by the camera.

        @param (str|AcquisitionMode): Acquisition mode as a string or an object

        Tested : yes
        SI check : yes
        """
        if self.module_state() == 'locked':
            self.log.error("Acquisition process is currently running : you can't change this parameter"
                           " until the acquisition is completely stopped ")
            return
        if isinstance(acquisition_mode, AcquisitionMode):
            acquisition_mode = acquisition_mode.name
        if acquisition_mode not in AcquisitionMode.__members__:
            self.log.error("Acquisition mode parameter do not match with any of the available acquisition "
                           "modes of the logic " )
            return
        self._acquisition_mode = acquisition_mode

    @property
    def camera_gain(self):
        """ Get the gain.

        @return: (float) exposure gain

        Tested : yes
        SI check : yes
        """
        return self._camera_gain

    @camera_gain.setter
    def camera_gain(self, camera_gain):
        """ Set the gain.

        @param camera_gain: (float) new gain to set to the camera preamplifier which must correspond to the
        internal gain list given by the constraints dictionary.


        Tested : yes
        SI check : yes
        """
        if self.module_state() == 'locked':
            self.log.error("Acquisition process is currently running : you can't change this parameter"
                           " until the acquisition is completely stopped ")
            return
        camera_gain = float(camera_gain)
        if not camera_gain in self.camera_constraints.internal_gains:
            self.log.error("Camera gain parameter do not match with any of the available camera internal gains ")
            return
        if camera_gain == self._camera_gain:
            return
        self.camera().set_gain(camera_gain)
        self._camera_gain = self.camera().get_gain()

    @property
    def exposure_time(self):
        """ Get the exposure time in seconds

        @return: (float) exposure time

        Tested : yes
        SI check : yes
        """
        return self._exposure_time

    @exposure_time.setter
    def exposure_time(self, exposure_time):
        """ Set the exposure time in seconds.

        @param exposure_time: (float) desired new exposure time

        Tested : yes
        SI check : yes
        """
        if self.module_state() == 'locked':
            self.log.error("Acquisition process is currently running : you can't change this parameter"
                           " until the acquisition is completely stopped ")
            return
        exposure_time = float(exposure_time)
        if not exposure_time > 0:
            self.log.error("Exposure time parameter must be a positive number ")
            return
        if exposure_time == self._exposure_time:
            return
        self.camera().set_exposure_time(exposure_time)
        self._exposure_time = self.camera().get_exposure_time()

    @property
    def scan_delay(self):
        """Getter method returning the scan delay between consecutive scan during multiple acquisition mode.

        @return: (float) scan delay

        Tested : yes
        SI check : yes
        """
        return self._scan_delay

    @scan_delay.setter
    def scan_delay(self, scan_delay):
        """Setter method setting the scan delay between consecutive scan during multiple acquisition mode.

        @param scan_delay: (float) scan delay

        Tested : yes
        SI check : yes
        """
        if self.module_state() == 'locked':
            self.log.error("Acquisition process is currently running : you can't change this parameter"
                           " until the acquisition is completely stopped ")
            return
        scan_delay = float(scan_delay)
        if not scan_delay >= 0:
            self.log.error("Scan delay parameter must be a positive number ")
            return
        if scan_delay == self._scan_delay:
            return
        self._scan_delay = scan_delay

    @property
    def number_of_scan(self):
        """Getter method returning the number of acquired scan during multiple acquisition mode.

        @return: (int) number of acquired scan

        """
        return self._number_of_scan

    @number_of_scan.setter
    def number_of_scan(self, number_scan):
        """Setter method setting the number of acquired scan during multiple acquisition mode.

        @param number_scan: (int) number of acquired scan

        """
        if self.module_state() == 'locked':
            self.log.error("Acquisition process is currently running : you can't change this parameter"
                           " until the acquisition is completely stopped ")
            return
        number_scan = int(number_scan)
        if not number_scan > 0:
            self.log.error("Number of acquired scan parameter must be positive ")
            return
        if number_scan == self._number_of_scan:
            return
        self._number_of_scan = number_scan

    ##############################################################################
    #                           Trigger mode functions
    ##############################################################################

    @property
    def trigger_mode(self):
        """Getter method returning the current trigger mode used by the camera.

        @return: (str) trigger mode (must be compared to the list)

        Tested : yes
        SI check : yes
        """
        return self._trigger_mode

    @trigger_mode.setter
    def trigger_mode(self, trigger_mode):
        """Setter method setting the trigger mode used by the camera.

        @param trigger_mode: (str) trigger mode

        Tested : yes
        SI check : yes
        """
        if self.module_state() == 'locked':
            self.log.error("Acquisition process is currently running : you can't change this parameter"
                           " until the acquisition is completely stopped ")
            return
        if isinstance(trigger_mode, TriggerMode):
            trigger_mode = trigger_mode.name
        if trigger_mode not in self.camera_constraints.trigger_modes:
            self.log.error("Trigger mode parameter do not match with any of available trigger "
                           "modes of the camera ")
            return
        if trigger_mode == self._trigger_mode:
            return
        self.camera().set_trigger_mode(trigger_mode)
        self._trigger_mode = self.camera().get_trigger_mode()

    ##############################################################################
    #                           Shutter mode functions (optional)
    ##############################################################################

    @property
    def shutter_state(self):
        """Getter method returning the shutter state.

        @return: (str) shutter state

        Tested : yes
        SI check : yes
        """
        if not self.camera_constraints.has_shutter:
            self.log.error("No shutter is available in your hardware ")
            return
        return self._shutter_state

    @shutter_state.setter
    def shutter_state(self, shutter_state):
        """Setter method setting the shutter state.

        @param shutter_state: (str) shutter state

        """
        if not self.camera_constraints.has_shutter:
            self.log.error("No shutter is available in your hardware ")
            return
        if self._shutter_state == shutter_state:
            return
        if isinstance(shutter_state, str) and shutter_state in ShutterState.__members__:
            shutter_state = ShutterState[shutter_state]
        if not isinstance(shutter_state, ShutterState):
            self.log.error("Shutter state parameter do not match with shutter states of the camera ")
            return
        self.camera().set_shutter_state(shutter_state)
        self._shutter_state = self.camera().get_shutter_state().name

    ##############################################################################
    #                           Temperature functions
    ##############################################################################

    @property
    def cooler_status(self):
        """Getter method returning the cooler status if ON or OFF.

        @return (bool): True if the cooler is on

        """
        if not self.camera_constraints.has_cooler:
            self.log.error("No cooler is available in your hardware ")
            return
        return self.camera().get_cooler_on()

    @cooler_status.setter
    def cooler_status(self, cooler_status):
        """ Setter method returning the cooler status if ON or OFF.

        @param (bool) value: True to turn it on, False to turn it off

        Tested : yes
        SI check : yes
        """
        if not self.camera_constraints.has_cooler:
            self.log.error("No cooler is available in your hardware ")
            return
        cooler_status = bool(cooler_status)
        self.camera().set_cooler_on(cooler_status)

    @property
    def camera_temperature(self):
        """ Getter method returning the temperature of the camera.

        @return (float): temperature (in Kelvin)

        """
        if not self.camera_constraints.has_cooler:
            self.log.error("No cooler is available in your hardware ")
            return
        return self.camera().get_temperature()

    @property
    def temperature_setpoint(self):
        """ Getter method for the temperature setpoint of the camera.

        @return (float): Current setpoint in Kelvin

        """
        if not self.camera_constraints.has_cooler:
            self.log.error("No cooler is available in your hardware ")
            return
        return self._temperature_setpoint

    @temperature_setpoint.setter
    def temperature_setpoint(self, value):
        """ Setter method for the the temperature setpoint of the camera.

        @param (float) value: New setpoint in Kelvin

        """
        if not self.camera_constraints.has_cooler:
            self.log.error("No cooler is available in your hardware ")
            return
        if value <= 0:
            self.log.error("Temperature setpoint can't be negative or 0 ")
            return
        self.camera().set_temperature_setpoint(value)
        self._temperature_setpoint = self.camera().get_temperature_setpoint()