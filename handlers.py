#!/usr/bin/env python
import requests
import xml.etree.ElementTree as ET
import json
from objectpath import *
import math

#Gets bus stop timetable data from Tampere City TKL open data API
class getNysse:      
    def __init__(self, monitoredstop):
        self._value = None
        self.monitoredstop = "5005"
        self.valid = False
    
    @property
    def value(self):
        return self._value
    
    def is_valid(self):
        if self.is_valid:
            if len(self._value) is not 0:
                if len(self._value["body"]) is not 0:
                    return True
        else:
            return False
    
    def update(self):
        apiurl = "http://data.itsfactory.fi/journeys/api/1/stop-monitoring?stops="
        url = apiurl + self.monitoredstop
        try:
            with requests.get(url) as req:
                data = json.loads(req.content)
                self._value = data
                self.valid = True
                return True
        except:
            self._value = None
            self.valid = False
            return False
            
#Gets current external radiation level from Finnish Meteorological Institute open data API
class getFMIradiation:    
    def __init__(self, location):
        self._value = float("NaN")
        self.location = "tampere"
        
    def __str__(self):
        if math.isnan(self._value):
            return "N/A"
        else:
            return "{0:.3f}".format(self._value)
    
    def __bool__(self):
        if math.isnan(self._value): return False
        else: return True
    
    @property
    def value(self):
        return self._value
    
    def update(self):
        stored_query = "stuk::observations::external-radiation::latest::simple"
        parameters = "DR_PT10M_avg"
    
        url = 'http://opendata.fmi.fi/' + 'wfs?service=WFS&version=2.0.0' + '&request=getFeature&storedquery_id=' +stored_query
        url += '&place='+self.location
        url += '&parameters='+parameters
        try:
            with requests.get(url) as req:
                #print(url.read().decode())
                xml = req.content
                tree = ET.ElementTree(ET.fromstring(xml))
                for el in tree.iter(tag='{http://xml.fmi.fi/schema/wfs/2.0}ParameterValue'):
                    val = el.text
                self._value = float(val)
                return True
        except:
            self._value = float("NaN")
            return False

#Gets current UV radiation index from Finnish Meteorological Institute open data API
class getFMI_UV_B:
    def __init__(self, station):
        self._value = float("NaN")
        self.station = "101339"
        
    def __str__(self):
        if math.isnan(self._value):
            return "N/A"
        else:
            return "{0:.1f}".format(self._value)
            
    def __bool__(self):
        if math.isnan(self._value): return False
        else: return True
    
    @property
    def value(self):
        return self._value    
     
    def update(self):
        stored_query = "fmi::observations::radiation::simple"
        parameters = "UVB_U"

        url = 'http://opendata.fmi.fi/' + 'wfs?service=WFS&version=2.0.0' + '&request=getFeature&storedquery_id=' +stored_query
        url += '&fmisid='+self.station
        url += '&parameters='+parameters
        try:
            with requests.get(url) as req:
                #print(url.read().decode())
                xml = req.content
                tree = ET.ElementTree(ET.fromstring(xml))
                for el in tree.iter(tag='{http://xml.fmi.fi/schema/wfs/2.0}ParameterValue'):
                    val = el.text
                self._value = float(val)
                return True
        except:
            self._value = float("NaN")
            return False
   
#Gets current weather warngings from Finnish Meteorological Institute closed API (will be opened in the future)
class getFMIwarnings:      
    def __init__(self, location):
        self._data = []
        self.valid = False
        self.location = "county.6"
        
    def __len__(self):
        return len(self._data)
    
    def warning_context(self, i):
        return self._data[i]["warning_context"]
    
    def effective_until(self, i):
        return self._data[i]["effective_until"]
    
    def causes(self, i):
        return self._data[i]["causes"]
    def severity(self, i):
        return self._data[i]["severity"]
        
    def is_valid(self):
        if self.valid:
            if len(self._data) is not 0:
                return True
        else:
            return False
    
    @property
    def value(self):
        return self._data
    
    def update(self):
        apikey = "Not open data yet!" #You have to get secret apikey for this one, hint: https://en.ilmatieteenlaitos.fi/warnings
        apiurl = "https://wms.fmi.fi/fmi-apikey/" + apikey + "/geoserver/alert/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=alert:weather_finland_active_all&maxFeatures=1000&outputFormat=application%2Fjson"
        #Parse data from json api with objectpath:
        expr = "$..*['{}' in @.reference and str(date()) in @.effective_from].(warning_context, effective_until, causes, severity)".format(self.location)
        try:
            with requests.get(apiurl) as req:
                _data = Tree(json.loads(req.content))
                ret = _data.execute(expr)
                self._data = list(ret)
                self.valid = True
                return True
        except:
            self._data = None
            self.valid = False
            return False