from src.core import Device, Parameter
from godirect import GoDirect
import numpy as np

class ThreeAxisMagnetometer(Device):
    """
    This class implements the Vernier GoDirect 3-Axis Magnetic Field Sensor
    Sensors:
    1. x-axis range:+-5mT, resolution:0.00015mT
    2. y-axis range:+-5mT, resolution:0.00015mT
    3. z-axis range:+-5mT, resolution:0.00015mT
    testing seems to indicate resolution is approx 0.01
    4. x-axis range:+-130mT, resolution:0.1mT
    5. y-axis range:+-130mT, resolution:0.1mT
    6. z-axis range:+-130mT, resolution:0.1mT
    Note: 5mT & 130mT are not at the same location in the wand and thus will read different values in a non-uniform field
    """
    _DEFAULT_SETTINGS = Parameter([Parameter('device_name','GDX-3MG 01007J6',str,'Name of sensor'),
                                   Parameter('connection_type','usb',['usb','bluetooth'],'Method to connect to sensor'),
                                   Parameter('sampling_rate',1000,int,'time between samples in milliseconds'),
                                   Parameter('precision','high',['high','low'],'high: +-5mT range with 0.00015mT resolution, low: +-130mT range with 0.1mT resolution'),
                                   Parameter('values',[
                                             Parameter('x',0,float,'x-axis value of sensor'),
                                             Parameter('y',0,float,'y-axis value of sensor'),
                                             Parameter('z',0,float,'y-axis value of sensor')
                                             ]),
                                   Parameter('round',5,int,'decimal places to round to; see sensor resolutions')
                                   ])

    def __init__(self, name=None, settings=None):
        super(ThreeAxisMagnetometer, self).__init__(name, settings)
        self._connect()

    def _connect(self):
        try:
            if self.settings['connection_type'] == 'usb':
                self.go_lib = GoDirect(use_ble=False, use_usb=True)
                self.dev = self.go_lib.get_device(threshold=-100)       #threshold is stength of bluetooth signal
                self.dev.open(auto_start=False)
                # enable readout of all sensors and pick out desired values within other methods
                self.dev.enable_sensors([1,2,3,4,5,6])
                self.enabled_sensors = self.dev.get_enabled_sensors()
                #clear all sensors
                self.dev.start()
                if self.dev.read():
                    for sensor in self.enabled_sensors:
                        # print(sensor.sensor_description + ": " + str(sensor.values))
                        sensor.clear()
                self.dev.stop()

            elif self.settings['connection_type'] == 'bluetooth':
                self.go_lib = GoDirect(use_ble=True, use_usb=False)     #switched T/F
                self.dev = self.go_lib.get_device(threshold=-100)
                self.dev.open(auto_start=False)
                self.dev.enable_sensors([1, 2, 3, 4, 5, 6])
                self.enabled_sensors = self.dev.get_enabled_sensors()
                self.dev.start()
                if self.dev.read():
                    for sensor in self.enabled_sensors:
                        # print(sensor.sensor_description + ": " + str(sensor.values))
                        sensor.clear()
                self.dev.stop()

        except OSError as error:
            print('No device found')
            raise




    def update(self, settings):
        super(ThreeAxisMagnetometer, self).update(settings)  # updates settings as per entered with method
        if self._settings_initialized:
            for key, value in settings.items():
                if key == 'connection_type':
                    self.go_lib.quit()
                    self._connect()
                elif key == 'device_name':
                    self.dev.set_name_from_advertisement(value)

    def single_measure(self, axis):
        value =[]
        self.dev.start(period=100)      #period set to 100 for fast, single measurement
        if self.dev.read():
            for sensor in self.enabled_sensors:
                # print(sensor.sensor_description + ": " + str(sensor.values))
                value.append(sensor.values[0])
                sensor.clear()
        self.dev.stop()

        index = self._axis_to_index(axis)
        value = round(value[index],self.settings['round'])
        return value

    def net_field(self, magnitude=False):
        data = []     #data is list (vector) of field ie. [x_component,y_component,z_component]
        self.dev.start(period=100)      #period set to 100 for fast, single measurement
        if self.dev.read():
            for sensor in self.enabled_sensors:
                # print(sensor.sensor_description + ": " + str(sensor.values))
                data.append(sensor.values[0])  # appends sensor value to list
                sensor.clear()
        self.dev.stop()
        rounded_values = [round(value,self.settings['round']) for value in data]

        if self.settings['precision'] == 'high':
            vector = rounded_values[:3]
        elif self.settings['precision'] == 'low':
            vector = rounded_values[3:6]

        result = np.array(vector)
        if magnitude:
            result = np.linalg.norm(vector)
        return result

    def sequence_measure(self, axes, period, num_points, precision=None):
        print('Estimated time: ',period*num_points/1000,' sec')
        self.dev.start(period=period)   #lowest period tested is 10 ms. This rate is controlled by the hardware
        data = {'X magnetic field':[],'Y magnetic field':[],'Z magnetic field':[],
                'X magnetic field 130mT':[],'Y magnetic field 130mT':[],'Z magnetic field 130mT':[]}

        if precision:
            self.settings['precision'] = precision
        if self.settings['precision'] == 'high':
            enabled_axes = [axis.capitalize() + ' magnetic field' for axis in axes]
            rounding = 5    #5mT sensors have 0.00015mT resolution
        elif self.settings['precision'] == 'low':
            enabled_axes = [axis.capitalize() + ' magnetic field 130mT' for axis in axes]
            rounding = 1    #130mT sensors have 0.1mT resolutoin

        while not all(len(values) >= num_points for values in data.values()):
        #takes sample at specified period until number of points is reached
            if self.dev.read():
                for sensor in self.enabled_sensors:
                    #print(sensor.sensor_description + ": " + str(sensor.values))
                    description = sensor.sensor_description
                    if description in data:
                        values = sensor.values
                        for item in values:
                            if len(data[description]) < num_points:
                                data[description].append(item)
                    sensor.clear()
        self.dev.stop()

        indexed_data = {key: data[key] for key in enabled_axes if key in data}
        rounded_data = {key: [round(value, rounding) for value in values] for key, values in indexed_data.items()}

        return rounded_data


    @property
    def is_connected(self):
        return self.dev.is_connected()



    def read_probes(self, key=None):
        assert(self._settings_initialized)
        assert key in list(self._PROBES.keys())

        if key == 'device_name':
            value = self.dev._name
        elif key == 'connection_type':
            value = self.settings['connection_type']
        elif key == 'net_field':
            value = self.net_field()

        return value

    def close(self):       #closes device effectivly reseting enabled sensors
        self.dev.close()
        self.go_lib.quit()

    def __del__(self):
        #at the end of running program quits out of godirect library
        self.go_lib.quit()

    @property
    def _PROBES(self):
        return {
            # ask device
            'device_name':'device name',
            'sensors':'list of sensors',
            'enabled_sensors':'sensors that have been enabled (default is x-axis +-5mT)',
            'godirect_version':'version of godirect loaded',
            'x_field':'value for x-axis',
            'y_field':'value for x-axis',
            'z_field':'value for x-axis',
            'net_field':'magnitude of field (sqrt(x^2+y^2+z^2))',
            # check code parameters
            'sampling_rate':'time between each sample in milliseconds',
            'connection_type':'usb or bluetooth',
        }

    def _axis_to_index(self, component):
        component = component.upper()
        if self.settings['precision'] == 'high':
            if component == 'X':
                return 0
            elif component == 'Y':
                return 1
            elif component == 'Z':
                return 2
            else:
                raise KeyError
        elif self.settings['precision'] == 'low':
            if component == 'X':
                return 3
            elif component == 'Y':
                return 4
            elif component == 'Z':
                return 5
            else:
                raise KeyError
        else:       #last key error probly not needed since precision can only be high/low
            raise KeyError

if __name__ == '__main__':
    sensor = ThreeAxisMagnetometer()
    #print(sensor.is_connected)
    print(sensor.read_probes(key='device_name'))
    print(sensor.net_field())
    sensor.update({'precision':'low'})

    print(sensor.read_probes('net_field'))
    print(sensor.single_measure('y'))
    print(sensor.sequence_measure(['x','y'],50,10,precision='high'))
    sensor.close()


