#!/usr/bin/env python3

import asyncio
from argh import arg
from ally import main


@arg("--name", help="Name to greet")
async def testme(name: str = "world"):
    print(f"Hello {name}")
    await asyncio.sleep(1)
    print("Bye now")

if __name__ == "__main__":
    main.run(testme)
    print("Done")
