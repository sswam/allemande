import asyncio
from argh import arg
from ally import main

async def testme():
    print("Hello, world")

if __name__ == "__main__":
    main.run(testme)
