#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr 17 21:18:10 2022

@author: dinesh
"""

import json
import datetime
from datetime import timedelta
import numpy as np
class weather_info:
    def __init__(self):
        self.weather_data = []
        self.weather_timesnaps = []
        self.cloud_data = []
        
    def find_nearest(self,array, value):
        array = np.asarray(array)
        idx = (np.abs(array - value)).argmin()
        return array[idx], idx
    
    def read_weather_from_json(self):
        # Opening JSON file
        weather_timesnaps = []
        weather_data = []
        for loop in range(6):
            f = open('/media/data2/walt_release/fifth_craig1/weather_data_'+str(loop+1)+'.json')
            data = json.load(f)
            for data_each in data['list']:
                self.weather_timesnaps.append(data_each['dt'])
                self.weather_data.append(data_each)
    
    
    def get_weather_data(self,img_paths):
        #img_paths = glob.glob('/media/data2/walt_release/fifth_craig3/2021-05/20*')
        for path in img_paths:
            #print(path.split('/')[-1].split('.j')[0])    
            try:
                time = datetime.datetime.strptime(path.split('/')[-1].split('.j')[0], "%Y-%m-%dT%H-%M-%S.%f")
            except:
                print(time, path.split('/')[-1].split('.j')[0])
                self.cloud_data.append(0)
                continue
            unix_time = datetime.datetime.timestamp(time- timedelta(hours=4))
            val, idx = self.find_nearest(self.weather_timesnaps,unix_time)
            
            if np.abs(unix_time- val) < 7200:
                    
                
                #print(time,unix_time, val, np.abs(unix_time- val))
                #if np.abs(unix_time- 1622217600) < 1000:
                #    print(self.weather_data[idx])
                #    asas
                #print(weather_data[idx]['clouds']['all'])
                self.cloud_data.append((self.weather_data[idx]['clouds']['all'] -50)/100)
    '''
    '''
