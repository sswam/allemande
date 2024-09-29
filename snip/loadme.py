# File: /home/sam/allemande/ally/loadme.py

from lazy import lazy
import os

__version__ = "0.1.0"  # Adding version number

# Lazy load modules
print(0)
lazy('openai')
print(1)
lazy('anthropic')
print(2)
lazy('claude')
print(4)
lazy('transformers', 'AutoTokenizer')
print(5)
lazy('datetime', _as='dtmod')
lazy('datetime', dt='datetime')

# Lazy load and initialize clients
lazy('openai', openai_async_client=lambda module: module.AsyncOpenAI())
print(6)

lazy('openai', perplexity_async_client=lambda module: module.AsyncOpenAI(
    base_url="https://api.perplexity.ai",
    api_key=os.environ.get("PERPLEXITY_API_KEY"),
))
print(7)

# Configure genai when it's first accessed
def configure_genai(module):
    module.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
    return module

lazy('google.generativeai', _as='genai', _=configure_genai)
print(8)

print()

print(f"{openai=}")
print(f"{anthropic=}")
print(f"{claude=}")
print(type(AutoTokenizer))
print(f"{AutoTokenizer=}")
print(dtmod)
print(dt)
print(dtmod.datetime.now())
print(dt.now())
print(f"{openai_async_client=}")
print(f"{perplexity_async_client=}")
print(f"{genai=}")

print()

print(f"{openai=}")
print(f"{anthropic=}")
print(f"{claude=}")
print(f"{AutoTokenizer=}")
print(f"{openai_async_client=}")
print(f"{perplexity_async_client=}")
print(f"{genai=}")
