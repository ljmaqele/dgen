#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import requests
from bs4 import BeautifulSoup
import pandas as pd

url = "https://github.com/NREL/dgen/wiki/Input-Sheet-Documentation"

# page = requests.get(url)
# soup = BeautifulSoup(page.content, "html.parser")
#print(page.text.split())

class DGenWikiProcessor(object):
    
    def __init__(self, 
                 url="https://github.com/NREL/dgen/wiki/Input-Sheet-Documentation",
                 ):
        
        self.url = None
        self.content = None
        self.__config__(url)
        
    def set(self, attr, value):
        
        self.__setattr__(attr, value)
        self.validate_property(attr)
        
    def get(self, attr):
        
        return self.__getattribute__(attr)
    
    def __config__(self, url):
        
        self.set('url', url)
        
    def validate_property(self, property_name):
        
        if property_name == 'url':
            try:
                page = requests.get(self.url)
                self.content = BeautifulSoup(page.content, "html.parser")
            except TypeError as e:
                raise TypeError("Invalid {0}: {1}".format(property_name, e))
        
    
    def scenario_options(self):
        
        raw_data = self.content.find_all('li')
        raw_data = [raw.text for raw in raw_data]
        data = pd.DataFrame({'raw_content':list(raw_data)})
        return data
    
    def body_content(self):
        return 1

if __name__=='__main__':
     
    page = DGenWikiProcessor()
    
    data = page.scenario_options()
        
        