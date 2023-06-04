from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from watchfiles import awatch
import asyncio
import os

async def speech_to_text(request: Request):
    form_data = await request.form()
    audio_file = form_data["file"]

    output_filename = "output.txt"  # Define your output filename here
    audio_filepath = "/path/to/save/audio/file.wav"  # Define your audio file path here

    with open(audio_filepath, "wb") as f:
        f.write(audio_file.file.read())

    # Wait for the output file to be created
    async for _ in awatch(output_filename):
        with open(output_filename, "r") as f:
            transcript = f.read()
            break

    return PlainTextResponse(transcript)

routes = [
    Route('/stt', speech_to_text, methods=['POST'])
]

middleware = [
    Middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])
]

app = Starlette(routes=routes, middleware=middleware)
