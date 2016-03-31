from polyglot.nodeserver_api import Node
import nest
from nest import utils as nest_utils
import sys
# REMOVE 
from login import USERNAME, PASSWORD


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
            self.parent.poly.LOGGER.info("Discovering Nest Products...")
            self.parent.poly.LOGGER.info("User: %s", USERNAME)
            self.napi = nest.Nest(USERNAME,PASSWORD, local_time=True)
            for structure in self.napi.structures:
                self.parent.poly.LOGGER.info('Structure   : %s' % structure.name)
                self.parent.poly.LOGGER.info(' Away        : %s' % structure.away)
                self.parent.poly.LOGGER.info(' Postal Code                    : %s' % structure.postal_code)
                self.parent.poly.LOGGER.info(' Country                        : %s' % structure.country_code)
                self.parent.poly.LOGGER.info(' dr_reminder_enabled            : %s' % structure.dr_reminder_enabled)
                self.parent.poly.LOGGER.info(' enhanced_auto_away_enabled     : %s' % structure.enhanced_auto_away_enabled)
                self.parent.poly.LOGGER.info(' eta_preconditioning_active     : %s' % structure.eta_preconditioning_active)
                self.parent.poly.LOGGER.info(' house_type                     : %s' % structure.house_type)
                self.parent.poly.LOGGER.info(' hvac_safety_shutoff_enabled    : %s' % structure.hvac_safety_shutoff_enabled)
                self.parent.poly.LOGGER.info(' num_thermostats                : %s' % structure.num_thermostats)
                self.parent.poly.LOGGER.info(' measurement_scale              : %s' % structure.measurement_scale)
                self.parent.poly.LOGGER.info(' renovation_date                : %s' % structure.renovation_date)
                self.parent.poly.LOGGER.info(' structure_area                 : %s' % structure.structure_area)
            for device in self.napi.devices:
                self.parent.poly.LOGGER.info('        Device: %s' % device.serial[-14:])
                self.parent.poly.LOGGER.info('        Where: %s' % device.where)
                self.parent.poly.LOGGER.info('            Mode     : %s' % device.mode)
                self.parent.poly.LOGGER.info('            Fan      : %s' % device.fan)
                self.parent.poly.LOGGER.info('            Temp     : %0.1fF' % nest_utils.c_to_f(device.temperature))
                self.parent.poly.LOGGER.info('            Humidity : %0.1f%%' % device.humidity)
                #self.parent.poly.LOGGER.info('            Target   : %0.1fF' % nest_utils.c_to_f(device.target))
                self.parent.poly.LOGGER.info('            Away Heat: %0.1fF' % nest_utils.c_to_f(device.away_temperature[0]))
                self.parent.poly.LOGGER.info('            Away Cool: %0.1fF' % nest_utils.c_to_f(device.away_temperature[1]))
                self.parent.poly.LOGGER.info('            hvac_ac_state         : %s' % device.hvac_ac_state)
                self.parent.poly.LOGGER.info('            hvac_cool_x2_state    : %s' % device.hvac_cool_x2_state)
                self.parent.poly.LOGGER.info('            hvac_heater_state     : %s' % device.hvac_heater_state)
                self.parent.poly.LOGGER.info('            hvac_aux_heater_state : %s' % device.hvac_aux_heater_state)
                self.parent.poly.LOGGER.info('            hvac_heat_x2_state    : %s' % device.hvac_heat_x2_state)
                self.parent.poly.LOGGER.info('            hvac_heat_x3_state    : %s' % device.hvac_heat_x3_state)
                self.parent.poly.LOGGER.info('            hvac_alt_heat_state   : %s' % device.hvac_alt_heat_state)
                self.parent.poly.LOGGER.info('            hvac_alt_heat_x2_state: %s' % device.hvac_alt_heat_x2_state)
                self.parent.poly.LOGGER.info('            hvac_emer_heat_state  : %s' % device.hvac_emer_heat_state)
                self.parent.poly.LOGGER.info('            online                : %s' % device.online)
                self.parent.poly.LOGGER.info('            last_ip               : %s' % device.last_ip)
                self.parent.poly.LOGGER.info('            local_ip              : %s' % device.local_ip)
                self.parent.poly.LOGGER.info('            last_connection       : %s' % device.last_connection)
                self.parent.poly.LOGGER.info('            error_code            : %s' % device.error_code)
                self.parent.poly.LOGGER.info('            battery_level         : %s' % device.battery_level)
                # ISY only allows 14 character limit on nodes, have to strip the serial number down to the last 14 chars. 
                address = device.serial[-14:].lower()
                lnode = self.parent.get_node(address)
                if not lnode:
                    self.parent.poly.LOGGER.info("New Thermostat Found.")
                    self.parent.thermostats.append(NestThermostat(self.parent, self.parent.get_node('nestcontrol'), 
                                                                      address, device.temperature, structure.name,  device.where, manifest))
            self.parent.update_config()
        except:
            e = sys.exc_info()[0]
            self.LOGGER.error('Nestcontrol _discover Caught general exception: %s', e)            
        return True

    _drivers = {}

    _commands = {'DISCOVER': _discover}
    
    node_def_id = 'nestcontrol'

class NestThermostat(Node):
    
    def __init__(self, parent, primary, address, temperature, structurename, location, manifest=None):
        self.parent = parent
        self.LOGGER = self.parent.poly.LOGGER
        self.structurename = structurename
        self.location = location
        try:
            self.napi = nest.Nest(USERNAME,PASSWORD, local_time=True)
        except:
            e = sys.exc_info()[0]
            self.LOGGER('NestThermostat __init__ Caught general exception: %s', e)            
        self.away = False
        self.online = False
        self.insidetemp = nest_utils.c_to_f(temperature)
        self.name = 'Nest ' + self.structurename + " " + self.location
        self.address = address
        self.LOGGER.info("Adding new Nest Device: %s Current Temp: %.1fF", self.name, self.insidetemp)
        super(NestThermostat, self).__init__(parent, address, self.name, primary, manifest)
        self.update_info()
        
    def update_info(self):
        try:
            for structure in self.napi.structures:
                if self.structurename == structure.name:
                    if structure.away:
                        self.away = True
            for device in self.napi.devices:
                if self.address == device.serial[-14:].lower():
                    self.mode = device.mode
                    self.online = device.online
                    self.insidetemp = nest_utils.c_to_f(device.temperature)
                    self.outsidetemp = nest_utils.c_to_f(self.napi.structures[0].weather.current.temperature)
                try:
                    self.targettemp = nest_utils.c_to_f(device.target[0])
                    self.LOGGER.info("Target Temp is a range between %.1f and %.1f - Displaying first number only due to ISY limitation", 
                                               nest_utils.c_to_f(device.target[0]), nest_utils.c_to_f(device.target[1]))
                except TypeError:
                    self.targettemp = nest_utils.c_to_f(device.target)
                self.LOGGER.info("Mode: %s InsideTemp: %.1fF OutsideTemp: %.1fF Target: %.1fF", 
                                           device.mode, nest_utils.c_to_f(device.temperature), self.outsidetemp, self.targettemp)
                # TODO, clean this up into a dictionary or something clever.
            if self.away:
                self.set_driver('ST', '13') 
            elif self.mode == 'range':
                self.set_driver('ST', '3')
            elif self.mode == 'heat':
                self.set_driver('ST', '1')
            elif self.mode == 'cool':
                self.set_driver('ST', '2')
            elif self.mode == 'fan':
                self.set_driver('ST', '6')
            else:
                self.set_driver('ST', '0')
            self.set_driver('GV1', self.insidetemp)
            self.set_driver('GV2', self.outsidetemp)
            self.set_driver('GV3', self.targettemp)
            self.set_driver('GV4', self.online)
        # Yes I know... but this helps me narrow down the specific Exceptions. python-nest module isn't great at error catching
        except:
            e = sys.exc_info()[0]
            self.LOGGER.error('NestThermostat update_info Caught general exception: %s', e)
        return

    def _setoff(self, **kwargs):
        try:
            for device in self.napi.devices:
                if self.address == device.serial[-14:].lower():       
                    device.mode = 'off'
        except:
            e = sys.exc_info()[0]
            self.LOGGER.error('NestThermostat _setoff Caught general exception: %s', e)
        return True        

    def _setauto(self, **kwargs):
        try:
            for device in self.napi.devices:
                if self.address == device.serial[-14:].lower():       
                    device.mode = 'range'
        except:
            e = sys.exc_info()[0]
            self.LOGGER.error('NestThermostat _setauto Caught general exception: %s', e)
        return True

    def _settemp(self, **kwargs):
        try:
            val = kwargs.get('value')
            if val:
                for device in self.napi.devices:
                    if self.address == device.serial[-14:].lower():
                        if device.mode == 'range':
                            self.LOGGER.info("Mode is ranged, Setting lower bound to %.1fF", val)
                            device.temperature = (nest_utils.f_to_c(val), device.target[1])
                        else:
                            self.LOGGER.info("Setting temperature to %.1fF.", val)                    
                            device.temperature = nest_utils.f_to_c(val)
                        self.set_driver('GV3', val, 17)
        except:
            e = sys.exc_info()[0]
            self.LOGGER('NestThermostat _settemp Caught general exception: %s', e)
        return True

    def _setmode(self, **kwargs):
        try:
            val = kwargs.get('value')
            newstate = NEST_STATES[int(val)]
            self.LOGGER.info('Got mode change request from ISY. Setting Nest to: %s', newstate)
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

            self.set_driver('ST', int(val))
        except:
            e = sys.exc_info()[0]
            self.LOGGER.error('NestThermostat _setauto Caught general exception: %s', e)
        return True

    def query(self, **kwargs):
        self.update_info()
        return True

    _drivers = {'GV1': [0, 17, myfloat], 'GV2': [0, 17, myfloat],
                'GV3': [0, 17, myfloat], 'GV4': [0, 2, int],
                'ST': [0, 67, int]}

    _commands = {'DON': _setauto,
                            'DOF': _setoff,
                            'MODE': _setmode,
                            'TEMP': _settemp}
                            
    node_def_id = 'nestdevice'