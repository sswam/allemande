#!/usr/bin/env python3
import asyncio
from starlette.applications import Starlette
from starlette.responses import JSONResponse, StreamingResponse
import uvicorn

app = Starlette()

@app.route("/whoami", methods=["GET"])
async def whoami(request):
	username = request.headers['X-Forwarded-User']
	return JSONResponse({"user": username})

@app.route("/post/{room}", methods=["POST"])
async def post(request):
	room = request.path_params['room']
	return JSONResponse({"message": f"Posting to room: {room}!"})

async def stream_data():
	for i in range(3):
		yield f"Data chunk {i}\n"
		await asyncio.sleep(1)

@app.route("/x/stream", methods=["GET"])
async def stream(request):
	return StreamingResponse(stream_data(), media_type="text/plain")

if __name__ == "__main__":
	uvicorn.run(app, host="127.0.0.1", port=8000)
