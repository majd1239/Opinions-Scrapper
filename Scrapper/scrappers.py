from bs4 import BeautifulSoup
from collections import ChainMap
from itertools import chain
from operator import itemgetter
from collections import defaultdict,namedtuple
from asyncio import ensure_future
import asyncio
import ujson


class Opinion:
    
    @classmethod
    async def create(cls, url, http_client):
        self = Opinion()
    
        self.http_client = http_client
        
        self.soup = BeautifulSoup(await self._get_url(url),'html.parser')
        
        self._url_prefix = "https://www.debate.org/"
        
        self._service_url = self._url_prefix + "opinions/~services/opinions.asmx/"
        
        self.data = defaultdict(dict)
        
        self.data["authorUrl"],self.data["opinion"],self.data["votes"] = self._getBasicInfo()
        
        self.data["responses"],self.responders = await self._getResponses()
        
        self.data["authorProfile"]  = await self._getAuthorProfile()
        
        return self
    
    async def _get_url(self,url):
        '''Download Url HTML Content'''
        
        async with self.http_client.get(url) as response:
            if response.status != 200: raise Exception("Invalid URL submitted")
            html = await response.read()
        
        return html
    
    def _get_text(self,html,query,within=True):
        '''Safely Extract Text from Html Element'''
        
        elem = html.find(**query) if within else html.find_next(**query)
        
        return elem.text if elem is not None else ""
        
    
    def _getBasicInfo(self):
        '''Get Opinion Title, Author URL and Votes Percentage'''
        
        self._info_html = self.soup.find(class_="debate-content")
        
        self.opinion_id = self._info_html.find(class_="cf",attrs={"id":"voting"}).get("did")
        
        opinion_title = self._get_text(self._info_html,{"class_":"q-title"})
        
        author_text = self._get_text(self._info_html,{"class_":"tags"})
        
        author_url = self._url_prefix + (author_text.split("Asked by:")[-1].strip()) if author_text!="" else ""
        
        votes = {label:self._getVote(label) for label in ["yes","no"]}
        
        return  author_url,opinion_title,votes
    
    def _getVote(self,label):
        '''Extract Vote Percentage from Html Element'''
        
        vote_text = self._get_text(self._info_html,{"class_":label+"-text"},False)
        
        return vote_text.split()[0]
    
    
    async def _extractResponse(self,response):
        '''Extract Response Title, Body, Responder Name and Comments from the Html Element'''
        
        keys = ["Title","Body","Responder","Likes","Comments"]
        
        schema = [{"name":"h2"},{"name":"p"},{"name":"cite"},{"class_":"l-cnt"},{"class_":"m-cnt"}]
        
        result = {}
        
        for key,elem in zip(keys,schema):
            value = self._get_text(response,elem)
            
            if key=="Comments":
                value = await self._getComments({"debateId":response.get("did"),"argId":response.get("aid"),"count":value,"allPast":False})
                
            result[key] = value if key!="Responder" else value.replace("Posted by: ",self._url_prefix)
            
        return result
  
    async def _getResponses(self):
        '''Get Votes Results and the Opinion Responses'''
        
        responses_html = self._info_html.find_next("div", {"id":"debate"})
        
        responses,responders = {},[]
        
        extra_responses = await self._getExtraRespones() if responses_html.find_next(class_="debate-more-btn") else {"yes":[],"no":[]}
            
        for label in ["yes","no"]:
            
            if self.data["votes"][label] == "0%":
                responses[label] = 'No responses have been submitted.'
                continue
            
            responses_elem = responses_html.find(class_="arguments args-"+label).find_all(class_="hasData") + extra_responses[label]

            responsesFutures = [ensure_future(self._extractResponse(response)) for response in responses_elem]

            responses[label] = await asyncio.gather(*responsesFutures)

            responders += [(label,author) for author in map(itemgetter("Responder"),responses[label]) if author!=""]
                
        return responses,responders
    
    async def _getExtraRespones(self,page_num=2,results=defaultdict(list)):
        '''Recursivley Fetch all Extra Responses Not Shown in the Html Page'''
        
        params = {"debateId": self.opinion_id,"pageNumber": page_num,"itemsPerPage": 10,"ysort": 5,"nsort": 5}
        
        async with self.http_client.post(self._service_url + "GetDebateArgumentPage",json=params) as response:
            assert response.status == 200
            out = await response.json()

        yes_html,no_html,status = out["d"].split('{ddo.split}')
        
        results["yes"]+= BeautifulSoup(yes_html,'html.parser').find_all(class_="hasData")
        
        results["no"]+= BeautifulSoup(no_html,'html.parser').find_all(class_="hasData")
        
        if status == 'finished':
            return results
        else:
            return await self._getExtraRespones(page_num+1,results)
    
    
    async def _getComments(self,params):
        '''Fetch all Comments Associated With a Response'''
        
        if params["count"]=='0': return []
        
        async with self.http_client.post(self._service_url + "GetComments",json=params) as response:
            assert response.status == 200
            out = await response.json()
       
        comments = ujson.loads(out["d"])["comments"]
        
        return [{"Content":text["Body"],"Commenter":text.get("MemberUserName","")} for text in comments]
        
    async def _getAuthorProfile(self):
        '''Get Opinon Author Profile Information'''
      
        if self.data["authorUrl"] == "": return {}
        
        async with self.http_client.get(self.data["authorUrl"]) as response:
            profile = Profile(await response.read())
        
        return  dict(profile.attributes._asdict())

    
class Profile:
    def __init__(self,html):
        self.soup = BeautifulSoup(html,'html.parser')
        
        self._profile =  self.soup.find("div", {"id":"profile"})
        
        Attributes = namedtuple("Attributes",["Info","Summary","Stats","Issues"])
        
        self.attributes = Attributes(self._getInfo(),self._getSummary(),self._getStats(),self._getIssues())

    def _getDemo(self,data):
        '''Get User Demoghraphics: Age, Gender, City, State and Country'''
        
        if data is None: return {}
        
        data,results = data.text, {}
            
        results["Age"] = data.split("-year")[0] if "year" in data else ""
        
        results["Gender"] = "" if "male" not in data else "female" if "female" in data else "male"
        
        location = data[data.find("in")+3:].strip(".").split(", ") if "in" in data else [None]*3
        
        results["City"],results["State"],results["Country"] = location
        
        return results
        
    def _getInfo(self):
        '''Get User Information: Demoghraphics, Eduction, Occupation..etc'''
            
        demo  = self._profile.find("div", {"id":"agl"})
       
        info = self._getDemo(demo)
        
        info_elem =  self._profile.find("div", {"id":"info"})
        
        if info_elem is None: return info
        
        for key,value in [elem.split(":") for elem in info_elem.text.replace("\n\n\n","\n\n").split("\n\n") if elem!=""]:
            if value in ["- Private -","No Answer","Not Saying","Prefer not to say"]: continue    
            
            info[key] = value
            
        return info 
    
    def _getIssues(self):
        '''Get User Stand on The Big Issues: Abortion,Gun Rights..etc'''
        
        issues_elem = self._profile.find("div", {"id":"issues"})
        
        if issues_elem is None: return {}
        
        issues = {}
        for issue_elem in issues_elem.find_all("tr"):
            issue = issue_elem.find("a").text
            
            stand = issue_elem.find(class_="c3").get_text(" ").split()[0]
            
            if stand not in ["Pro","Con"]: continue
                
            issues[issue] = stand
            
        return issues
            
    def _getSummary(self):
        '''Get User Interests Summary: About Me, Music, Movies, Tv Shows..etc '''
        
        summary_html =  self._profile.find("div", {"id":"summaries"})
        
        if summary_html is None: return {}
        
        strip = str.maketrans('\r', ' ',"\n")
        
        summary = {}
        for key,value in zip(summary_html.find_all(class_="left"),summary_html.find_all(class_="right")):
            summary[key.text] = value.text.translate(strip)
        
        return summary
    
    def _getStats(self):
        '''Get User Activity and Debate Statistics'''
        
        stats_html = self._profile.find_all("table",{"id":"stats"})
        
        if len(stats_html)==0: {}
        
        data = chain(*[stat_html.find_all("tr") for stat_html in stats_html])
        
        strip = str.maketrans('', '',",%")
        
        stats = {}
        for key,value in [elem.text.split(":") for elem in data if ":" in elem.text]:
            stats[key] = float(value.translate(strip))
        
        return stats