import json
import os,time

import unittest
import requests

class Tests(unittest.TestCase):
    ''' Unit testcases for REST APIs '''
        
    def test_health(self):
        response = requests.get("http://0.0.0.0:5000/health")
        self.assertEqual(response.status_code,200)
        self.assertIsNone(json.loads(response.content.decode()).get("Error"))
        
    def test_info(self):
        response = requests.get("http://0.0.0.0:5000/info")
        self.assertEqual(response.status_code,200)
        self.assertIsNone(json.loads(response.content.decode()).get("Error"))
        
    def test_empty_opinion(self):
        url = "https://www.debate.org/opinions/should-students-be-off-th-day-after-veterand-day"
        
        response = requests.post("http://0.0.0.0:5000/opinion_scraper",json={"url":url})
        
        self.assertEqual(response.status_code,200)
        
        results = json.loads(response.content.decode())
        
        self.assertEqual(results.get("opinion"),"Should Students Be Off Th Day After Veterand Day?")
        
        votes = results.get('votes')
        responses = results.get('responses')
        
        self.assertIsNotNone(votes)
        self.assertIsNotNone(responses)
        
        for label in ["yes","no"]:
            self.assertEqual(votes.get(label),"0%")
            self.assertEqual(responses.get(label),'No responses have been submitted.')
                             
        self.assertEqual(results.get('authorUrl'),"")
        self.assertEqual(results.get('authorProfile'),{})

    def test_popular_opinion(self):
        url = 'https://www.debate.org/opinions/is-cyber-bullying-a-real-problem'
                             
        response = requests.post("http://0.0.0.0:5000/opinion_scraper",json={"url":url})
        
        self.assertEqual(response.status_code,200)
        
        results = json.loads(response.content.decode())
        
        self.assertEqual(results.get("opinion"),'Is cyber bullying a real problem?')
        
        votes = results.get('votes')
        responses = results.get('responses')
        
        self.assertIsNotNone(votes)
        self.assertIsNotNone(responses)
        
        for label in ["yes","no"]:
            self.assertTrue(votes.get(label)!="0%")
            self.assertTrue(len(responses.get(label))>20)  
            self.assertTrue(any([response.get('Comments')[0].get("Content")!='' for response in responses.get(label) if len(response.get('Comments'))>0]))
            
        for key in ['authorUrl','authorProfile']:
            self.assertTrue(results.get(key)!="")
            
        author_profile = results.get("authorProfile")
        
        self.assertTrue(author_profile.get('Issues') == {'Animal Rights': 'Con'})
        self.assertTrue(author_profile.get('Info')['Age'] == '23')
        stats_keys = set(['Debates', 'Lost', 'Tied', 'Won', 'Win Ratio', 'Percentile', 'Elo Ranking', 'Forum Posts',
                      'Votes Cast', 'Opinion Arguments', 'Opinion Questions', 'Poll Votes', 'Poll Topics'])
        self.assertTrue(set(author_profile.get('Stats').keys()) == stats_keys)
        
        
        
        
if __name__ == '__main__':
    
    unittest.main()