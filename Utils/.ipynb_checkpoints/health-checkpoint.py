import os,sys
sys.path.append(os.getcwd().rsplit("/",1)[0])
import time,os
import asyncio
from enum import Enum
from singleton_decorator import singleton
from bs4 import BeautifulSoup
from Scrapper.scrappers import Opinion

HEALTH_INTERVAL = 360.0

DEBATE_URL = "https://www.debate.org/"

class HealthStatus(str, Enum):
    Red = 'Red'
    Green = 'Green'


class HealthResult:
    def __init__(self):
        self.status = None
        self.factors = {}

    def update(self,status,factors):
        if self.status!=status:
            self.factors={}
            
        self.status = status.name
        self.factors.update(factors)
        

@singleton        
class Health():

    def __init__(self, app=None,loop=None):
        
        self.http_client,self.loop = app.http, loop
        
        self._health = HealthResult()
        
        asyncio.set_event_loop(loop)
        
        app.add_task(self.Health_Run)
 
    @property
    def health(self):
        return self._health.__dict__
    
    async def health_test(self,url):
        return await Opinion.create(url, self.http_client)
    
    def check_results(self,task):
        if task.cancelled() is True: return
        
        opinion  = task.result()
        
        if opinion is None:
            self._health.update(HealthStatus.Red, {"up": False,"test_url":self.opinion_url, "reason": "Uknown"})
            
        else:
            self._health.update(HealthStatus.Green,{"up":True,"test_url":self.opinion_url})
            
    async def create_test(self):
        
        async with self.http_client.get(DEBATE_URL) as response:
            soup = BeautifulSoup(await response.read(),'html.parser')
        
        self.opinion_url = DEBATE_URL + soup.find("ul",{"id":"opinions-list"}).find('a')['href']
            
        task = self.loop.create_task(self.health_test(self.opinion_url))
        
        task.add_done_callback(self.check_results)
        
        return task
    
    async def Health_Run(self):
        while(True):
            try:
                await asyncio.wait_for(self.create_test(),timeout=10)
                
            except Exception as e:
                self._health.update(HealthStatus.Red, {"up": False,"test_url":self.opinion_url, "reason": str(e)})
            
            await asyncio.sleep(HEALTH_INTERVAL)
    
            
        

   