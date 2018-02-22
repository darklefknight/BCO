"""
This Module contains the Radiation class. This class is for easy working with the Radiation data.
"""

import sys
import bz2
import glob
import numpy as np
from datetime import timedelta

from BCO.tools import tools
from BCO.Instruments.Device_module import __Device,getValueFromSettings

try:
    from netCDF4 import Dataset
except:
    print("The module netCDF4 needs to be installed for the BCO-package to work.")
    sys.exit(1)


class Radiation(__Device):
    """

    """

    def __init__(self, start, end):

        self.start = self._checkInputTime(start) + timedelta(hours=0)
        self.end = self._checkInputTime(end) + timedelta(hours=0)
        self.path = self.__getPath()
        print(self.path)

        # Attributes:
        self.title = None
        self.devices = None
        self.temporalResolution = None
        self.location = None

        self.lat = None
        self.lon = None

        self.__getAttributes()

    def __getAttributes(self):
        """
        Function to load the static attributes from the netCDF file.
        """
        _date = self.start.date()
        _datestr = _date.strftime("%Y%m%d")
        _nameStr = "%s/Radiation__Deebles_Point__DownwellingRadiation__1s__%s.nc.bz2" % (_datestr[:-2], _datestr)
        # _file = glob.glob(self.path + _datestr + "/" +  _nameStr)[0]
        _file = glob.glob(self.path + _nameStr)[0]

        if "bz2" in _file[-5:]:
            nc = tools.bz2Dataset(_file)
        else:
            nc = Dataset(_file)
        self.title = nc.title
        self.devices = nc.devices
        self.temporalResolution = nc.resolution.split(";")[0]
        self.location = nc.location
        nc.close()

        self.lat = self.__getValueFromNc("lat")
        self.lon = self.__getValueFromNc("lon")

    def __getValueFromNc(self, value: str):
        """
        This function gets values from the netCDF-Dataset, which stay constant over the whole timeframe. So its very
        similar to __getArrayFromNc(), but without the looping.

        Args:
            value: A string for accessing the netCDF-file.
                    For example: 'LWdown_diffuse'

        Returns:
            Numpy array
        """
        _date = self.start.date()
        _datestr = _date.strftime("%Y%m%d")
        _nameStr = "%s/Radiation__Deebles_Point__DownwellingRadiation__1s__%s.nc.bz2" % (_datestr[:-2], _datestr)
        _file = glob.glob(self.path + _nameStr)[0]

        if "bz2" in _file[-5:]:
            nc = tools.bz2Dataset(_file)
        else:
            nc = Dataset(_file)

        _var = nc.variables[value][:].copy()
        nc.close()

        return _var


    def getTime(self):
        """
        Loads the time steps over the desired timeframe from all netCDF-files and returns them as one array.

        Returns:
            A numpy array containing datetime.datetime objects

        Example:
            Getting the time-stamps from an an already initiated Radiation object 'rad':

            >>> rad.getTime()
        """

        time = self.__getArrayFromNc('time')

        time = tools.num2time(time)  # converting seconds since 1970 to datetime objects
        time = self._local2UTC(time)


        return time

    def getRadiation(self,scope,direction,scattering):

        directions = ["down"]
        scopes = ["LW","SW"]
        scatterings = ["direct","diffuse","global"]




    def __getArrayFromNc(self, value):
        """
        Retrieving the 'value' from the netCDF-Dataset reading just the desired timeframe.

        Args:
            value: String which is a valid key for the Dataset.variables[key].

        Returns:
            Numpy array with the values of the desired key and the inititated time-window.

        Example:
            What behind the scenes happens for an example-key 'VEL' is something like:

            >>> nc = Dataset(input_file)
            >>> _var = nc.variables["VEL"][self.start:self.end].copy()

            Just that in this function we are looping over all files and in the end concatinating them.
        """
        var_list = []
        skippedDates = []
        for _date in tools.daterange(self.start.date(), self.end.date()):
            _datestr = _date.strftime("%Y%m%d")
            _nameStr = "%s/Radiation__Deebles_Point__DownwellingRadiation__1s__%s.nc.bz2"%(_datestr[:-2],_datestr)
            # _file = glob.glob(self.path + _datestr + "/" + _nameStr)[0]
            _file = glob.glob(self.path + _nameStr)[0]
            try:
                if "bz2" in _file[-5:]:
                    nc = tools.bz2Dataset(_file)
                else:
                    nc = Dataset(_file)

                # print(_date)
                _start, _end = self._getStartEnd(_date, nc)
                # print(_start,_end)
                if _end != 0:
                    varFromDate = nc.variables[value][_start:_end].copy()
                else:
                    varFromDate = nc.variables[value][_start:].copy()
                var_list.append(varFromDate)
                nc.close()
            except:
                skippedDates.append(_date)
                continue

        _var = var_list[0]
        if len(var_list) > 1:
            for item in var_list[1:]:
                _var = np.concatenate((_var, item))

        if skippedDates:
            self._FileNotAvail(skippedDates)

        return _var


    def get_nc(self):
        for _date in tools.daterange(self.start.date(), self.end.date()):
            _datestr = _date.strftime("%Y%m%d")
            _nameStr = "%s/Radiation__Deebles_Point__DownwellingRadiation__1s__%s.nc.bz2"%(_datestr[:-2],_datestr)
            print(self.path + _nameStr)
            # _file = glob.glob(self.path + _datestr + "/" + _nameStr)[0]
            _file = glob.glob(self.path + _nameStr)[0]
            if "bz2" in _file[-5:]:
                nc = tools.bz2Dataset(_file)
            else:
                nc = Dataset(_file)
        return nc


    def __getPath(self):
        """
        Reads the Path from the settings.ini file by calling the right function from Device_module.

        Returns: Path of the Radiation data.

        """
        return getValueFromSettings("RADIATION_PATH")