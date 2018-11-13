from locust import HttpLocust, TaskSet, task,seq_task

class UserBehavior(TaskSet):
    @task(1)
    def short_opinion(self):
        self.client.headers['Content-Type'] = "application/json"
        response = self.client.post("/opinion_scraper",json={"url":"https://www.debate.org/opinions/should-drug-users-be-put-in-prison"})

        
    @task(1)
    def long_opinion(self):
        self.client.headers['Content-Type'] = "application/json"
        response = self.client.post("/opinion_scraper",json={"url":'https://www.debate.org/opinions/should-the-fcc-repeal-net-neutrality'})

        
class WebsiteUser(HttpLocust):
    task_set = UserBehavior
    min_wait = 0
    max_wait = 0