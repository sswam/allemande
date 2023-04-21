#!/usr/bin/env python3 
from starlette.applications import Starlette
from starlette.responses import JSONResponse
import uvicorn

app = Starlette()

@app.route("/hello/{name}", methods=["GET"])
async def hello(request):
    name = request.path_params['name']
    return JSONResponse({"message": f"Hello, {name}!"})

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
