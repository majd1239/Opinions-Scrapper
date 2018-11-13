from sanic import Sanic
from sanic.response import json
from Scrapper.scrappers import Opinion
from Utils.harness import Harness
from multiprocessing import cpu_count
app = Sanic(__name__)


@app.route('/opinion_scraper', methods=['POST'])
async def opinion_scraper(request):
    
    url = request.json.get("url")
    
    opinion = await Opinion.create(url, app.http)

    return json(opinion.data)

if __name__ == "__main__":
    Harness(app)
    app.run(host='0.0.0.0', port=5000,workers=cpu_count())