# -*- coding: utf-8 -*-

"""
Note pour le groupe de dév. au L2C :
l'ensemble des fonctions de camera_interface.py a été repris ici.
d'autres fonctions correspondant à une camera science ont été ajoutées
"""

from core.interface import abstract_interface_method
from core.meta import InterfaceMetaclass


class L2CSpectrometerInterface(metaclass=InterfaceMetaclass):
    """This is the Interface class to define the controls for the simple
    optical spectrometer.
    """

    @abstract_interface_method
    def get_camera_constraints(self):
        """
        Note pour moi :
        detailler ici toutes les clés de lecture des contraintes
        les contraintes doivent permettre de répondre à la question : qu'est ce que tu supportes
        Par exemple : est ce que tu supportes le mode multi_spec ?
        est-ce que tu supportes un gain reglable ? et dans quelle gamme...
        """
        pass

    @abstract_interface_method
    def get_name(self):
        """ Retrieve an identifier of the camera that the GUI can print

        @return string: name for the camera
        """
        pass

    @abstract_interface_method
    def get_size(self):
        """ Retrieve size of the image in pixel

        @return tuple: Size (width, height)
        """
        pass

    @abstract_interface_method
    def support_live_acquisition(self):
        """ Return whether or not the camera can take care of live acquisition

        @return bool: True if supported, False if not
        """
        pass

    @abstract_interface_method
    def start_live_acquisition(self):
        """ Start a continuous acquisition

        @return bool: Success ?
        """
        pass

    @abstract_interface_method
    def start_single_acquisition(self):
        """ Start a single acquisition

        @return bool: Success ?
        """
        pass

    @abstract_interface_method
    def stop_acquisition(self):
        """ Stop/abort live or single acquisition

        @return bool: Success ?
        """
        pass

    @abstract_interface_method
    def set_exposure(self, exposure):
        """ Set the exposure time in seconds

        @param float time: desired new exposure time

        @return float: setted new exposure time
        """
        pass

    @abstract_interface_method
    def set_readout_rate(self, readout_rate):
        pass

    @abstract_interface_method
    def set_temperature(self, temperature):
        pass

    @abstract_interface_method
    def set_obtu_behaviour(self, obtu_behaviour):
        pass

    @abstract_interface_method
    def set_gain(self, gain):
        """ Set the gain

        @param float gain: desired new gain

        @return float: new exposure gain
        """
        pass

    @abstract_interface_method
    def set_acquisition_mode(self, acquisition_mode):
        pass

    @abstract_interface_method
    def set_binning_x(self, bin_x):
        pass

    @abstract_interface_method
    def set_binning_y(self, bin_y):
        pass

    @abstract_interface_method
    def set_region_of_interest(self, x1, y1, x2, y2):
        pass

    @abstract_interface_method
    def set_multi_spec(self, ):
        pass

    @abstract_interface_method
    def set_background_mode(self, bg_mode):
        pass

###############################################

    @abstract_interface_method
    def get_exposure(self):
        """ Get the exposure time in seconds

        @return float exposure time
        """
        pass

    @abstract_interface_method
    def get_readout_rate(self, readout_rate):
        pass

    @abstract_interface_method
    def get_temperature(self, temperature):
        pass

    @abstract_interface_method
    def get_obtu_behaviour(self, obtu_behaviour):
        pass

    @abstract_interface_method
    def get_gain(self):
        """ Get the gain

        @return float: exposure gain
        """
        pass

    @abstract_interface_method
    def get_acquisition_mode(self, acquisition_mode):
        pass

    @abstract_interface_method
    def get_binning_x(self, bin_x):
        pass

    @abstract_interface_method
    def get_binning_y(self, bin_y):
        pass

    @abstract_interface_method
    def get_region_of_interest(self, x1, y1, x2, y2):
        pass

    @abstract_interface_method
    def get_multi_spec(self, ):
        pass

    @abstract_interface_method
    def get_background_mode(self, bg_mode):
        pass

    @abstract_interface_method
    def get_camera_status(self, spectrometer_status):
        pass

    @abstract_interface_method
    def get_acquired_data(self):
        """ Return an array of last acquired image.

        @return numpy array: image data in format [[row],[row]...]

        Each pixel might be a float, integer or sub pixels
        """
        pass

    @abstract_interface_method
    def get_ready_state(self):
        """ Is the camera ready for an acquisition ?

        @return bool: ready ?
        """
        pass

