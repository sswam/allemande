#!/usr/bin/env python3-allemande

"""
Interface for local language models through the Ally portals system.
"""

import logging
from pathlib import Path

from ally import main, logs, portals  # type: ignore
from settings import LOCAL_AGENT_TIMEOUT

__version__ = "0.1.0"

logger = logs.get_logger()


async def request_local_model(
    portal_name: str,
    input_text: str,
    config: dict | None = None,
    timeout: float = LOCAL_AGENT_TIMEOUT,
) -> str:
    """Send a request to a local model through a portal and get the response."""
    portal = portals.get_portal(portal_name)

    req = await portal.prepare_request(config)
    req_input = req / "request.txt"
    req_input.write_text(input_text, encoding="utf-8")

    await portal.send_request(req)

    resp, status = await portal.wait_for_response(req, timeout=timeout)

    if status == "error":
        await portal.response_error(resp)  # raises RuntimeError

    new = resp / "new.txt"
    new_text = new.read_text(encoding="utf-8") if new.exists() else ""

    await portal.remove_response(resp)

    return new_text


async def achat_local(messages: list[dict], model_config: dict) -> dict:
    """Chat with a local model, compatible with llm.py interface."""
    # Convert messages to simple text format for local models
    fulltext_parts = []

    for msg in messages:
        role = msg["role"]
        content = msg["content"]

        if role == "system":
            fulltext_parts.append(f"System:\t{content}")
        elif role == "user":
            fulltext_parts.append(f"User:\t{content}")
        elif role == "assistant":
            fulltext_parts.append(f"Assistant:\t{content}")

    # Add invitation for the model to respond
    model_name = model_config.get("name", "Assistant")
    fulltext_parts.append(f"{model_name}:")

    fulltext = "\n".join(fulltext_parts)

    # Get config for the request
    config = model_config.get("config", {}).copy()
    config["model"] = model_config.get("id", model_config.get("name"))

    # Add generation parameters if specified
    if "temperature" in model_config:
        config["temperature"] = model_config["temperature"]
    if "max_tokens" in model_config:
        config["max_tokens"] = model_config["max_tokens"]
    if "stop" in model_config:
        config["stop_sequences"] = model_config["stop"]

    # Get the portal service name
    service = model_config.get("service", "llm_llama")

    logger.debug("Requesting from local model: %s", config.get("model"))

    response_text = await request_local_model(
        service,
        fulltext,
        config=config,
        timeout=model_config.get("timeout", LOCAL_AGENT_TIMEOUT)
    )

    return {
        "role": "assistant",
        "content": response_text.strip()
    }


def setup_args(arg):
    """Set up command-line arguments for testing."""
    arg("prompt", nargs="*", help="prompt to send to the model")
    arg("-m", "--model", help="local model name")
    arg("-s", "--service", help="portal service name")


async def test_local(prompt: list[str], model: str = "default", service: str = "llm_llama") -> None:
    """Test function for local model requests."""
    if not prompt:
        prompt = ["Hello! Please introduce yourself."]

    prompt_text = " ".join(prompt)
    print(f"Prompt: {prompt_text}")
    print("-" * 40)

    messages = [{"role": "user", "content": prompt_text}]
    model_config = {
        "name": model,
        "id": model,
        "service": service,
    }

    response = await achat_local(messages, model_config)
    print(f"Response: {response['content']}")


if __name__ == "__main__":
    main.go(test_local, setup_args)

# <think>
# The user wants me to create a `llm_local.py` module that:
# 1. Provides async functionality for local models
# 2. Is styled like the hello_py.py example
# 3. Can be integrated into llm.py to support 'local' models
# 4. Uses a simplified version of code from local_agents.py (making portal requests)
#
# Looking at local_agents.py, the key function is `client_request` which:
# - Takes a portal, input_text, config, and timeout
# - Prepares a request, writes the input text
# - Sends the request and waits for response
# - Returns the new text and response path
#
# The main integration point would be adding a new vendor "local" to the MODELS dict in llm.py, and then adding an achat_local function.
#
# I should keep it simple, avoid deep nesting, use modern Python features, and follow the style guide.
# </think>
#
# Here's `llm_local.py`:

# Now, here's how to integrate this into `llm.py`. Add these changes:
#
# 1. First, add the import near the top with other local imports:

# import llm_local

# 2. Add local model definitions to the MODELS dictionary:

#     "local-llama": {
#         "aliases": ["llama"],
#         "vendor": "local",
#         "service": "llama",
#         "description": "Local Llama model",
#         "cost_in": 0,
#         "cost_out": 0,
#     },
#     "local-mistral": {
#         "aliases": ["mistral"],
#         "vendor": "local",
#         "service": "mistral",
#         "description": "Local Mistral model",
#         "cost_in": 0,
#         "cost_out": 0,
#     },

# 3. In the `allm_chat` function, add a new vendor case before the final `raise ValueError`:

#     if vendor == "local":
#         return await llm_local.achat_local(messages, model)

# That's it! With these changes, you can now use local models through llm.py like:

# echo "user: Hello!" | llm chat -m local-llama

# The simplified version:
# - Removes all the complex context handling and agent-specific logic
# - Focuses just on making portal requests and returning responses
# - Uses a simple text format for messages instead of complex preprocessing
# - Maintains compatibility with the llm.py interface
#
# This will allow local_agents.py to be simplified later to use llm.py instead of duplicating the portal request logic.
