from polyglot.nodeserver_api import Node
import nest
import requests
from nest import utils as nest_utils
import sys
from login import USERNAME, PASSWORD

# Globally disable SSL warnings from requests package.
requests.packages.urllib3.disable_warnings()


NEST_STATES = {0: "off", 1: "heat", 2: "cool", 3: "range", 13: "away"}

def myfloat(value, prec=2):
    """ round and return float """
    return round(float(value), prec)

class NestControl(Node):
    
    def __init__(self, *args, **kwargs):
        super(NestControl, self).__init__(*args, **kwargs)
    
    def _discover(self, **kwargs):
        try:
            manifest = self.parent.config.get('manifest', {})
            self.parent.poly.logger.info("Discovering Nest Products...")
            self.parent.poly.logger.info("User: %s", USERNAME)
            self.napi = nest.Nest(USERNAME,PASSWORD, cache_ttl=30, local_time=True)
            for structure in self.napi.structures:
                try:
                    self.parent.poly.logger.info('Structure   : %s' % structure.name)
                    """
                    self.parent.poly.logger.info(' Away        : %s' % structure.away)
                    self.parent.poly.logger.info(' Postal Code                    : %s' % structure.postal_code)
                    self.parent.poly.logger.info(' Country                        : %s' % structure.country_code)
                    self.parent.poly.logger.info(' dr_reminder_enabled            : %s' % structure.dr_reminder_enabled)
                    self.parent.poly.logger.info(' enhanced_auto_away_enabled     : %s' % structure.enhanced_auto_away_enabled)
                    self.parent.poly.logger.info(' eta_preconditioning_active     : %s' % structure.eta_preconditioning_active)
                    self.parent.poly.logger.info(' house_type                     : %s' % structure.house_type)
                    self.parent.poly.logger.info(' hvac_safety_shutoff_enabled    : %s' % structure.hvac_safety_shutoff_enabled)
                    self.parent.poly.logger.info(' num_thermostats                : %s' % structure.num_thermostats)
                    self.parent.poly.logger.info(' measurement_scale              : %s' % structure.measurement_scale)
                    self.parent.poly.logger.info(' renovation_date                : %s' % structure.renovation_date)
                    self.parent.poly.logger.info(' structure_area                 : %s' % structure.structure_area)
                    """
                except TypeError as e:
                    self.parent.poly.logger.info('Nestcontrol _discover Caught exception: %s', e)
            for device in self.napi.devices:
                try:
                    self.parent.poly.logger.info('Device: %s' % device.serial[-14:])
                    """
                    self.parent.poly.logger.info('        Where: %s' % device.where)
                    self.parent.poly.logger.info('            Mode     : %s' % device.mode)
                    self.parent.poly.logger.info('            Fan      : %s' % device.fan)
                    self.parent.poly.logger.info('            Temp     : %0.1fF' % nest_utils.c_to_f(device.temperature))
                    self.parent.poly.logger.info('            Humidity : %0.1f%%' % device.humidity)
                    self.parent.poly.logger.info('            Away Heat: %0.1fF' % nest_utils.c_to_f(device.away_temperature[0]))
                    self.parent.poly.logger.info('            Away Cool: %0.1fF' % nest_utils.c_to_f(device.away_temperature[1]))
                    self.parent.poly.logger.info('            hvac_ac_state         : %s' % device.hvac_ac_state)
                    self.parent.poly.logger.info('            hvac_cool_x2_state    : %s' % device.hvac_cool_x2_state)
                    self.parent.poly.logger.info('            hvac_heater_state     : %s' % device.hvac_heater_state)
                    self.parent.poly.logger.info('            hvac_aux_heater_state : %s' % device.hvac_aux_heater_state)
                    self.parent.poly.logger.info('            hvac_heat_x2_state    : %s' % device.hvac_heat_x2_state)
                    self.parent.poly.logger.info('            hvac_heat_x3_state    : %s' % device.hvac_heat_x3_state)
                    self.parent.poly.logger.info('            hvac_alt_heat_state   : %s' % device.hvac_alt_heat_state)
                    self.parent.poly.logger.info('            hvac_alt_heat_x2_state: %s' % device.hvac_alt_heat_x2_state)
                    self.parent.poly.logger.info('            hvac_emer_heat_state  : %s' % device.hvac_emer_heat_state)
                    self.parent.poly.logger.info('            online                : %s' % device.online)
                    self.parent.poly.logger.info('            last_ip               : %s' % device.last_ip)
                    self.parent.poly.logger.info('            local_ip              : %s' % device.local_ip)
                    self.parent.poly.logger.info('            last_connection       : %s' % device.last_connection)
                    self.parent.poly.logger.info('            error_code            : %s' % device.error_code)
                    self.parent.poly.logger.info('            battery_level         : %s' % device.battery_level)
                    """
                except TypeError as e:
                    self.parent.poly.logger.info('Nestcontrol _discover Caught exception: %s', e)
                # ISY only allows 14 character limit on nodes, have to strip the serial number down to the last 14 chars. 
                address = device.serial[-14:].lower()
                lnode = self.parent.get_node(address)
                if not lnode:
                    self.parent.poly.logger.info("New Thermostat Found.")
                    self.parent.thermostats.append(NestThermostat(self.parent, self.parent.get_node('nestcontrol'), 
                                                                      address, device.temperature, structure.name,  device.where, manifest))
            self.parent.update_config()
        except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError, TypeError) as e:
            self.logger.error('Nestcontrol _discover Caught exception: %s', e)
        return True
        
    def query(self, **kwargs):
        self.parent.report_drivers()
        return True

    _drivers = {}

    _commands = {'DISCOVER': _discover}
    
    node_def_id = 'nestcontrol'

class NestThermostat(Node):
    
    def __init__(self, parent, primary, address, temperature, structurename, location, manifest=None):
        self.parent = parent
        self.logger = self.parent.poly.logger
        self.structurename = structurename
        self.location = location
        try:
            self.logger.info('Initializing New Thermostat')
            self.napi = nest.Nest(USERNAME,PASSWORD, local_time=True)
        except requests.exceptions.HTTPError as e:
            self.logger.error('NestThermostat __init__ Caught exception: %s', e)            
        self.away = False
        self.online = False
        self.insidetemp = nest_utils.c_to_f(temperature)
        try:
            self.name = 'Nest ' + self.structurename + " " + self.location
        except TypeError as e:
            self.logger.error('Caught TypeError on structurename or location, which means they don\'t exist. Using Generic name.')
            self.name = 'Nest Thermostat'
        self.address = address
        self.logger.info("Adding new Nest Device: %s Current Temp: %i F", self.name, self.insidetemp)
        super(NestThermostat, self).__init__(parent, address, self.name, primary, manifest)
        self.update_info()
        
    def update_info(self):
        self.away = False
        try:
            self._checkconnect()
            self.logger.info("First structure update: %s", self.napi.structures[0].away)
            for structure in self.napi.structures:
                if self.structurename == structure.name:
                    if structure.away:
                        self.away = True
            for device in self.napi.devices:
                if self.address == device.serial[-14:].lower():
                    self.mode = device.mode
                    if device.fan:
                        self.set_driver('CLIFS', '1')
                    else:
                        self.set_driver('CLIFS', '0')
                    self.online = device.online
                    self.humidity = device.humidity
                    if device.hvac_ac_state:
                        self.state = '2'
                    elif device.hvac_heater_state:
                        self.state = '1'
                    else:
                        self.state = '0'
                    self.insidetemp = int(round(nest_utils.c_to_f(device.temperature)))
                    try:
                        self.outsidetemp = int(round(nest_utils.c_to_f(self.napi.structures[0].weather.current.temperature)))
                    except (TypeError) as e:
                        self.logger.error('NestThermostat update_info Caught an exception: %s', e)
                        self.outsidetemp = 0
                    if self.mode == 'range':
                        self.targetlow = int(round(nest_utils.c_to_f(device.target[0])))
                        self.targethigh = int(round(nest_utils.c_to_f(device.target[1])))
                        self.logger.info("Target Temp is a range between %i F and %i F", 
                                               self.targetlow, self.targethigh)
                    else:
                        self.targetlow = int(round(nest_utils.c_to_f(device.target)))
                        self.logger.info('Target Temp is %i F', self.targetlow)
                        self.targethigh = self.targetlow

                        # TODO, clean this up into a dictionary or something clever.
                    self.logger.info("Away %s: Mode: %s InsideTemp: %i F OutsideTemp: %i F TargetLow: %i F TargetHigh: %i F", 
                                                   self.away, self.mode, self.insidetemp, self.outsidetemp, self.targetlow, self.targethigh)
                    if self.away:
                        self.set_driver('CLIMD', '13') 
                    elif self.mode == 'range':
                        self.set_driver('CLIMD', '3')
                    elif self.mode == 'heat':
                        self.set_driver('CLIMD', '1')
                    elif self.mode == 'cool':
                        self.set_driver('CLIMD', '2')
                    elif self.mode == 'fan':
                        self.set_driver('CLIMD', '6')
                    else:
                        self.set_driver('CLIMD', '0')
                    self.set_driver('ST', int(self.insidetemp))
                    self.set_driver('CLISPC', self.targethigh)
                    self.set_driver('CLISPH', self.targetlow)
                    self.set_driver('CLIHUM', self.humidity)
                    self.set_driver('CLIHCS', self.state)
                    self.set_driver('GV2', self.outsidetemp)
                    self.set_driver('GV4', self.online)
        except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError) as e:
            self.logger.error('NestThermostat update_info Caught exception: %s', e)
        return

    def _setoff(self, **kwargs):
        try:
            for device in self.napi.devices:
                if self.address == device.serial[-14:].lower():       
                    device.mode = 'off'
        except requests.exceptions.HTTPError as e:
            self.logger.error('NestThermostat _setoff Caught exception: %s', e)
        return True        

    def _setauto(self, **kwargs):
        try:
            for device in self.napi.devices:
                if self.address == device.serial[-14:].lower():       
                    device.mode = 'range'
        except requests.exceptions.HTTPError as e:
            self.logger.error('NestThermostat _setauto Caught exception: %s', e)
        return True

    def _checkconnect(self):
        try:
            connected = self.napi.devices[0].online
            self.logger.info('Connected: %s', connected)
            if not connected:
                self.napi = nest.Nest(USERNAME,PASSWORD, local_time=True)
            return True
        except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError, TypeError) as e:
            self.logger.error('CheckConnect: %s', e)
            return False

    def _setmode(self, **kwargs):
        try:
            val = kwargs.get('value')
            if self._checkconnect():
                newstate = NEST_STATES[int(val)]
                self.logger.info('Got mode change request from ISY. Setting Nest to: %s', newstate)
                if newstate == 'away':  
                    for structure in self.napi.structures:
                        if self.structurename == structure.name:
                            structure.away = True
                else:
                    for structure in self.napi.structures:
                        if self.structurename == structure.name:
                            structure.away = False
                            self.away = False
                    for device in self.napi.devices:
                        if self.address == device.serial[-14:].lower():       
                            device.mode = newstate
                self.set_driver('CLIMD', int(val))
                #self.update_info()
        except requests.exceptions.HTTPError as e:
            self.logger.error('NestThermostat _setauto Caught exception: %s', e)
        return True

    def _setfan(self, **kwargs):
        try:
            val = int(kwargs.get('value'))
            if self._checkconnect():
                for device in self.napi.devices:
                    if self.address == device.serial[-14:].lower():
                        if val == 1:
                            device.fan = True
                            self.logger.info('Got Set Fan command. Setting fan to \'On\'')
                        else:
                            device.fan = False
                            self.logger.info('Got Set Fan command. Setting fan to \'Auto\'')
                        self.set_driver('CLIFS', val)
        except requests.exceptions.HTTPError as e:
            self.logger.error('NestThermostat _settemp Caught exception: %s', e)
        return True

    def _sethigh(self, **kwargs):
        inc = False
        try:
            try:
                val = int(kwargs.get('value'))
            except TypeError:
                inc = True
            self._checkconnect()
            for device in self.napi.devices:
                if self.address == device.serial[-14:].lower():
                    if device.mode == 'range':
                        if not inc:
                            device.temperature = (device.target[0], nest_utils.f_to_c(val))
                            self.logger.info("Mode is ranged, Setting upper bound to %i F", val)
                        else:
                            val = int(nest_utils.c_to_f(device.target[1]) + 1)
                            self.logger.info("Mode is ranged, incrementing upper bound to %i F", val)
                            device.temperature = (device.target[0], nest_utils.f_to_c(val))
                    else:
                        self.logger.info("Setting temperature to %i F.", val)
                        if not inc:
                            device.temperature = int(nest_utils.f_to_c(val))
                        else:
                            val = int(nest_utils.c_to_f(device.target) + 1)
                            device.temperature = nest_utils.f_to_c(val)
                    self.set_driver('CLISPC', val)
        except requests.exceptions.HTTPError as e:
            self.logger.error('NestThermostat _settemp Caught exception: %s', e)
        return True

    def _setlow(self, **kwargs):
        inc = False
        try:
            try:
                val = int(kwargs.get('value'))
            except TypeError:
                inc = True
            self._checkconnect()
            for device in self.napi.devices:
                if self.address == device.serial[-14:].lower():
                    if device.mode == 'range':
                        if not inc:
                            device.temperature = (nest_utils.f_to_c(val), device.target[1])
                            self.logger.info("Mode is ranged, Setting lower bound to %i F", val)
                        else:
                            val = int(round(nest_utils.c_to_f(device.target[0]) - 1))
                            self.logger.info("Mode is ranged, decrementing lower bound to %i F", val)
                            device.temperature = (nest_utils.f_to_c(val), device.target[1])
                    else:
                        self.logger.info("Setting temperature to %i F.", val)
                        if not inc:
                            device.temperature = nest_utils.f_to_c(val)
                        else:
                            val = int(round(nest_utils.c_to_f(device.target) - 1))
                            device.temperature = nest_utils.f_to_c(val)
                    self.set_driver('CLISPH', val)
        except requests.exceptions.HTTPError as e:
            self.logger.error('NestThermostat _settemp Caught exception: %s', e)
        return True

    def _beep(self, **kwargs):
        return True

    def query(self, **kwargs):
        self.update_info()
        self.report_driver()
        return True

    _drivers = {
                'CLIMD': [0, 67, int], 'CLISPC': [0, 14, int],
                'CLISPH': [0, 14, int], 'CLIFS':[0, 99, int],
                'CLIHUM':[0, 51, int], 'CLIHCS':[0, 66, int],
                'GV1': [0, 14, int], 'GV2': [0, 14, int],
                'GV3': [0, 14, int], 'GV4': [0, 2, int],
                'ST': [0, 14, int]}

    _commands = {'DON': _setauto,
                            'DOF': _setoff,
                            'CLIMD': _setmode,
                            'CLIFS': _setfan,
                            'BRT': _sethigh,
                            'DIM': _setlow,
                            'BEEP': _beep,
                            'CLISPH': _setlow,
                            'CLISPC': _sethigh,
                            'QUERY': query}
                            
    node_def_id = 'nestthermostat'