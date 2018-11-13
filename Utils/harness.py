from sanic import Sanic
from sanic.response import json
import os,sys,time
import traceback
from Utils.health import Health
from aiohttp import ClientSession

class Harness:

    def __init__(self, app: Sanic):
        
        @app.listener('before_server_start')
        async def aiohttpSetup(app, loop):
            session = ClientSession(loop=loop)
            app.http = session
            
        @app.listener('before_server_start')
        async def healthSetup(app, loop):
            Health(app,loop)
    
        @app.route('/ping')
        async def ping(request):
            return json({
                'message': 'pong',
                'timestamp': time.time()
            })
        
        @app.route('/health')
        async def health(request):
            return json(Health().health)
        
        @app.route('/info')
        async def info(request):
            return json({
                'request': request,
                'env': dict(os.environ),
                'path': sys.path,
                'prefix': sys.prefix,
                'args': sys.argv,
                'version': sys.version
            })

        @app.exception(Exception)
        def routeExceptions(request, exception):
            return json("Error: {}".format(str(traceback.format_exc())), status=500)