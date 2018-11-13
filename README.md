# Opinions-Scrapper

Fully asynchronous rest api that scrappes any opinoin from https://www.debate.org/opinions/.

Usage:

```shell
curl --header "Content-Type: application/json" --request POST \
--data '{"url":"http://www.debate.org/opinions/should-drug-users-be-put-in-prison"}' \
http://localhost:5000/opinion_scraper
```

## Performance:

![Screenshot](imgs/latency.png)

#### Average latency is 715ms for requests having short and long opinions.

![Screenshot](imgs/concurrency.png.png)

![Screenshot](imgs/graph.png)

#### Average throughput is 6.4 req/s for 10 concurrent users calling the endpoint with an average response  time of 1.5s. This
#### is with a 4 Core machine running 4 sanic workers. It scales horizantally nicely with a 1.5x factor.



