#!/usr/bin/env python3
import asyncio
from starlette.applications import Starlette
from starlette.responses import JSONResponse, StreamingResponse
import uvicorn

app = Starlette()

ADMINS = ["sam"]

@app.route("/x/whoami", methods=["GET", "POST"])
async def whoami(request):
	# TODO admin might depend on the room
	user = request.headers['X-Forwarded-User']
	admin = user in ADMINS
	return JSONResponse({"user": user, "admin": admin})

@app.route("/x/post", methods=["POST"])
async def post(request):
	# room = request.path_params['room']
	print(request)
	return JSONResponse({"message": f"Posting"})

async def stream_data():
	for i in range(3):
		yield f"Data chunk {i}\n"
		await asyncio.sleep(1)

@app.route("/x/stream", methods=["GET"])
async def stream(request):
	return StreamingResponse(stream_data(), media_type="text/plain")

if __name__ == "__main__":
	uvicorn.run(app, host="127.0.0.1", port=8000)
