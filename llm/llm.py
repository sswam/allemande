#!/usr/bin/env python3-allemande

"""
llm.py: A simple wrapper for various language model APIs including OpenAI ChatGPT,
Anthropic's Claude, Perplexity, and Google models.

This module implements a wrapper for various language model APIs, providing a
unified interface for interacting with different models. It includes functions
for chatting, querying, processing text, and counting tokens. The code uses
async programming for efficient API calls and includes error handling and
retrying mechanisms.
"""

# Import necessary modules
import sys
from sys import stdin, stdout, stderr
import os
import logging
import re
from typing import IO
from math import inf
import time
import random
from pathlib import Path
import textwrap
import asyncio
import json
import io

from argh import arg
import tab
import tiktoken
from slug import slug

from ally import main, titty
from ally.lazy import lazy
import tsv2txt_py as tsv2txt
import llm_vision

# Lazy imports for API clients
lazy("openai", "AsyncOpenAI")
lazy("openai", openai_async_client=lambda openai: openai.AsyncOpenAI())
lazy(
    "openai",
    perplexity_async_client=lambda openai: openai.AsyncOpenAI(
        base_url="https://api.perplexity.ai",
        api_key=os.environ.get("PERPLEXITY_API_KEY"),
    ),
)
lazy(
    "openai",
    xai_async_client=lambda openai: openai.AsyncOpenAI(
        base_url="https://api.x.ai/v1",
        api_key=os.environ.get("XAI_API_KEY"),
    ),
)
lazy(
    "openai",
    deepseek_async_client=lambda openai: openai.AsyncOpenAI(
        base_url="https://api.deepseek.com",
        api_key=os.environ.get("DEEPSEEK_API_KEY"),
    ),
)
lazy(
    "openai",
    openrouter_async_client=lambda openai: openai.AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ.get("OPENROUTER_API_KEY"),
    ),
)


lazy("anthropic")
lazy("claude")

lazy(
    "google.genai",
    _as="google_genai",
    google_client=lambda google_genai: google_genai.Client(
        api_key=os.environ.get("GOOGLE_API_KEY")
    ),
)

lazy("vertexai.preview.tokenization", _as="google_tokenization")

lazy("transformers", "AutoTokenizer")
llama3_tokenizer = None


__version__ = "0.1.4"

# Set up logging
logger = logging.getLogger(__name__)

# Define settings and constants
LOGDIR = Path(os.environ["HOME"]) / "llm.log"
LOGFILE_NAME_MAX_LEN = 255
RETRIES = 20
exceptions_to_retry = (
    "RateLimitError",
    "APIConnectionError",
    "InternalServerError",
    "ServiceUnavailableError",
    "TimeoutError",
    "APIError",
)

default_model = "claude"
default_model_small = "gemini-2.0-flash"

# Define available models and their properties
MODELS = {
    "o3": {
        "aliases": ["op", "grace"],
        "id": "o3-2025-04-16",
        "vendor": "openai",
        "vision": True,
        "description": "OpenAI's strongest reasoning model, with complex reasoning",
        "cost_in": 10,
        "cost_out": 40,
        "no_stop": True,
        "temp_min": 1,
        "temp_max": 1,
    },
    "o4-mini": {
        "aliases": ["om", "fermi"],
        "vendor": "openai",
        "vision": True,
        "description": "OpenAI's faster, cheaper reasoning model.",
        "cost_in": 3,
        "cost_out": 12,
        "no_stop": True,
        "temp_min": 1,
        "temp_max": 1,
    },
    "gpt-4": {
        "aliases": ["4", "emmy"],
        "vendor": "openai",
        "vision": True,
        "id": "gpt-4.1",
#        "id": "gpt-4.1-2025-04-14",
#        "id": "gpt-4o-2024-11-20",
        "description": "OpenAI's GPT-4.1 is an advanced multimodal model.",
        "cost_in": 2.5,
        "cost_out": 10,
    },
    "gpt-4.1-mini": {
        "aliases": ["4m", "dav", "davinci"],
        "vendor": "openai",
        "vision": True,
        "description": "OpenAI's GPT-4.1 mini is a cost-efficient model.",
        "cost_in": 0.15,
        "cost_out": 0.6,
    },
    "claude-opus": {
        "aliases": ["co", "claudo"],
        "vendor": "anthropic",
        "vision": True,
        "id": "claude-opus-4-20250514",
#        "id": "claude-3-7-sonnet-latest",
        "description": "Claude 4 Opus is Anthropic's strongest model.",
        "cost_in": 15,
        "cost_out": 75,
    },
    "claude-sonnet": {
        "aliases": ["cn", "clauden"],
        "vendor": "anthropic",
        "vision": True,
        "id": "claude-sonnet-4-20250514",
#        "id": "claude-3-7-sonnet-latest",
        "description": "Claude 4 Sonnet is Anthropic's latest mid-size model.",
        "cost_in": 3,
        "cost_out": 15,
    },
    "claude": {
        "aliases": ["c", "claud"],
        "vendor": "anthropic",
        "vision": True,
        "id": "claude-3-5-sonnet-latest",
        "description": "Claude 3.5 Sonnet is Anthropic's strong and reliable model.",
        "cost_in": 3,
        "cost_out": 15,
    },
    "claude-haiku": {
        "aliases": ["i", "clia"],
        "vendor": "anthropic",
        "vision": True,
        "id": "claude-3-haiku-20240307",
        "description": "Claude 3 Haiku is Anthropic's fastest and most affordable model.",
        "cost_in": 0.25,
        "cost_out": 1.25,
    },
    "gemini-2.5-pro": {
        "aliases": ["gemmi-paid", "gemini", "gp"],
        "vendor": "google",
        "vision": True,
        "api_key": "GOOGLE_API_KEY",
        "id": "gemini-2.5-pro-preview-03-25",
#        "id": "gemini-2.5-pro-preview-03-25",
        "description": "Google's strongest Gemini model with a 1 million context window and 64K output.",
        "cost_in": 1.25,
        "cost_out": 10,
    },
    "gemini-2.5-pro-free": {
        "aliases": ["gemmi", "gemmi-free", "gemini-free"],
        "vendor": "google",
        "vision": True,
        "api_key": "GOOGLE_API_KEY_FREE",
        "id": "gemini-2.5-pro-exp-03-25",
        "description": "Google's strongest Gemini model with a 1 million context window and 64K output.",
        "cost_in": 0,
        "cost_out": 0,
    },
    "gemini-2.5-pro-openrouter": {
        "aliases": ["gemmi-openrouter"],
        "vendor": "openrouter",
        "vision": True,
        "id": "google/gemini-2.5-pro-exp-03-25:free",
        "description": "Google's strongest Gemini model with a 1 million context window and 64K output.",
        "cost_in": 0,
        "cost_out": 0,
    },
    "gemini-2.5-flash": {
        "aliases": ["gf", "flasho"],
        "id": "models/gemini-2.5-flash-preview-04-17",
        "vendor": "google",
        "vision": True,
        "description": "Google's fast thinking model with a 1 million context window.",
        "cost_in": 0.15,
        "cost_out": 0.6,
    },
    "gemini-2.0-flash-lite": {
        "aliases": ["lite"],
        "vendor": "google",
        "vision": True,
        "description": "Google's fastest model with a 1 million context window.",
        "cost_in": 0.075,
        "cost_out": 0.3,
    },
    "gemini-2.0-flash": {
        "aliases": ["flashi"],
        "vendor": "google",
        "vision": True,
        "description": "Google's fast model with a 1 million context window.",
        "cost_in": 0.1,
        "cost_out": 0.4,
    },
    "sonar-reasoning-pro": {
        "aliases": ["sageri"],
        "vendor": "perplexity",
        "description": "Perplexity's Sonar Resoning Pro model, with 127K context and online access.",
        "cost_req": 5,
        "cost_in": 2,
        "cost_out": 8,
    },
    "sonar-reasoning": {
        "aliases": ["sonari"],
        "vendor": "perplexity",
        "description": "Perplexity's Sonar Resoning model, with 127K context and online access.",
        "cost_req": 5,
        "cost_in": 1,
        "cost_out": 5,
    },
    "sonar-pro": {
        "aliases": ["sagi"],
        "vendor": "perplexity",
        "description": "Perplexity's Sonar Pro model, with 300K context and online access.",
        "cost_req": 5,  # per thousand
        "cost_in": 3,
        "cost_out": 15,
    },
    "sonar": {
        "aliases": ["sona"],
        "vendor": "perplexity",
        "description": "Perplexity's Sonar model, with 127K context and online access.",
        "cost_req": 5,
        "cost_in": 1,
        "cost_out": 1,
    },
    "grok2": {
        "vendor": "xai",
        "aliases": ["grok"],
        "id": "grok-2-latest",
        "description": "xAI's Grok 2 model, with 128K context and a sense of humour",
        "cost_in": 2,
        "cost_out": 10,
    },
    "grok3": {
        "vendor": "xai",
        "aliases": ["rocki"],
        "id": "grok-3-beta",
        "description": "xAI's Grok 3 model, with 128K context and a sense of humour",
        "cost_in": 3,
        "cost_out": 15,
    },
    "deepseek-chat": {
        "aliases": ["dese"],
        "vendor": "deepseek",
        "description": "deepseek-chat points to DeepSeek-V3",
        "cost_in": 0.27,
        "cost_out": 1.10,
    },
    "deepseek-reasoner": {
        "aliases": ["deseri"],
        "vendor": "deepseek",
        "description": "deepseek-reasoner points to DeepSeek-R1",
        "cost_in": 0.55,
        "cost_out": 2.19,
    },
    "llama-4-scout-free": {
        "aliases": ["scout-free", "skout-free"],
        "vendor": "openrouter",
        "id": "meta-llama/llama-4-scout:free",
        "description": "Llama 4 Scout",
        "cost_in": 0,
        "cost_out": 0,
    },
    "llama-4-maverick-free": {
        "aliases": ["maverick-free", "mavi-free"],
        "vendor": "openrouter",
        "id": "meta-llama/llama-4-maverick:free",
        "description": "Llama 4 Maverick",
        "cost_in": 0,
        "cost_out": 0,
    },
    "llama-4-scout": {
        "aliases": ["scout", "skout"],
        "vendor": "openrouter",
        "id": "meta-llama/llama-4-scout",
        "description": "Llama 4 Scout",
        "cost_in": 0,
        "cost_out": 0,
    },
    "llama-4-maverick": {
        "aliases": ["maverick", "mavi"],
        "vendor": "openrouter",
        "id": "meta-llama/llama-4-maverick",
        "description": "Llama 4 Maverick",
        "cost_in": 0,
        "cost_out": 0,
    },
    "gemma-3-27b-free": {
        "aliases": ["gemma-free"],
        "vendor": "openrouter",
        "id": "google/gemma-3-27b-it:free",
        "description": "Gemma 3 27B",
        "cost_in": 0,
        "cost_out": 0,
    },
    "gemma-3-27b": {
        "aliases": ["gemma"],
        "vendor": "openrouter",
        "id": "google/gemma-3-27b-it",
        "description": "Gemma 3 27B",
        "cost_in": 0,
        "cost_out": 0,
    },
    "gemma-3-12b-free": {
        "aliases": ["gemma-12b-free"],
        "vendor": "openrouter",
        "id": "google/gemma-3-12b-it:free",
        "description": "Gemma 3 12B",
        "cost_in": 0,
        "cost_out": 0,
    },
    "gemma-3-12b": {
        "aliases": ["gemma-12b"],
        "vendor": "openrouter",
        "id": "google/gemma-3-12b-it",
        "description": "Gemma 3 12B",
        "cost_in": 0,
        "cost_out": 0,
    },
    "gemma-3-4b-free": {
        "aliases": ["gemma-4b-free"],
        "vendor": "openrouter",
        "id": "google/gemma-3-4b-it:free",
        "description": "Gemma 3 4B",
        "cost_in": 0,
        "cost_out": 0,
    },
    "gemma-3-4b": {
        "aliases": ["gemma-4b"],
        "vendor": "openrouter",
        "id": "google/gemma-3-4b-it",
        "description": "Gemma 3 4B",
        "cost_in": 0,
        "cost_out": 0,
    },
    "gemma-3-1b-free": {
        "aliases": ["gemma-1b-free"],
        "vendor": "openrouter",
        "id": "google/gemma-3-1b-it:free",
        "description": "Gemma 3 1B",
        "cost_in": 0,
        "cost_out": 0,
    },
    "gemma-3-1b": {
        "aliases": ["gemma-1b"],
        "vendor": "openrouter",
        "id": "google/gemma-3-1b-it",
        "description": "Gemma 3 1B",
        "cost_in": 0,
        "cost_out": 0,
    },
    "qwq-32b": {
        "aliases": ["qwen"],
        "vendor": "openrouter",
        "id": "qwen/qwq-32b:free",
        "description": "Qwen: QwQ 23B (free)",
        "cost_in": 0,
        "cost_out": 0,
    },
    "eva-qwen2.5-72b": {
        "aliases": ["eva"],
        "vendor": "openrouter",
        "id": "eva-unit-01/eva-qwen-2.5-72b",
        "description": "EVA Qwen2.5 72B",
        "cost_in": 0.9,
        "cost_out": 1.2,
    },
    "mistral-large": {
        "aliases": ["misti"],
        "vendor": "openrouter",
        "id": "mistralai/mistral-large-2411",
        "description": "Mistral Large 2411",
        "cost_in": 2,
        "cost_out": 6,
    },
}


def setup_models():
    """Set up the models and their aliases."""
    global default_model, default_model_small  # pylint: disable=global-statement
    for name, model in MODELS.items():
        if "id" not in model:
            model["id"] = name

    # Set default models from environment variables if available
    env_llm_model = os.environ.get("ALLEMANDE_LLM_DEFAULT")
    env_llm_model_small = os.environ.get("ALLEMANDE_LLM_DEFAULT_SMALL")

    if env_llm_model in MODELS:
        default_model = env_llm_model
    if env_llm_model_small in MODELS:
        default_model_small = env_llm_model_small

    MODELS[default_model]["aliases"] += ["default", "d"]
    MODELS[default_model_small]["aliases"] += ["small", "s"]


setup_models()


ALLOWED_ROLES = ["user", "assistant", "system"]

DEFAULT_TEMPERATURE = 1
CLAUDE_MAX_TEMPERATURE = 1
OPENAI_MAX_TEMPERATURE = 2
GOOGLE_MAX_TEMPERATURE = 2
TOKEN_LIMIT = inf

os.environ["HF_HUB_OFFLINE"] = "1"


def load_huggingface_by_plan(what, plan, loader):  # pylint: disable=too-many-branches
    """Try to load gated Hugging Face models, like Llama, from alternative sources"""
    saved_hf_hub_offline = os.environ.get("HF_HUB_OFFLINE", "1")
    for online, model_name in plan:
        try:
            logger.debug("Trying to load %s from %s, online=%s", what, model_name, online)
            os.environ["HF_HUB_OFFLINE"] = str(int(not online))
            resource = loader(model_name)
            break
        except IOError as ex:
            logger.debug("  Failed to load %s from %s, online=%s: %s", what, model_name, online, ex)
    else:
        raise IOError(f"Failed to load {what} from huggingface")
    os.environ["HF_HUB_OFFLINE"] = saved_hf_hub_offline
    return resource


def get_llama3_tokenizer():
    """Get the Llama3 tokenizer ... somehow"""
    global AutoTokenizer, llama3_tokenizer  # pylint: disable=global-statement
    if not llama3_tokenizer:
        # The offiical model is gated, need to register; seems a bit much for a tokenizer.
        plan = [
            (0, "meta-llama/Meta-Llama-3-8B"),
            (0, "baseten/Meta-Llama-3-tokenizer"),
            (1, "meta-llama/Meta-Llama-3-8B"),
            (1, "baseten/Meta-Llama-3-tokenizer"),
        ]
        llama3_tokenizer = load_huggingface_by_plan("llama3_tokenizer", plan, AutoTokenizer.from_pretrained)
    return llama3_tokenizer


# Mock completion for testing
fake_completion = {
    "choices": [
        {
            "finish_reason": "stop",
            "index": 0,
            "message": {
                "content": '\n\nSure, Sam! Here\'s a dad joke for you: "Why did the tomato turn red? Because it saw the salad dressing!"',
                "role": "assistant",
            },
        }
    ],
    "created": 1678809131,
    "id": "chatcmpl-6u1EZ06waciROkpOqDHVdi2HtL3iX",
    "model": "gpt-3.5-turbo-0301",
    "object": "chat.completion",
    "usage": {"completion_tokens": 104, "prompt_tokens": 24, "total_tokens": 128},
}


def get_model_by_alias(model):
    """Get the full model name from an alias"""
    abbrev_models = [k for k, v in MODELS.items() if model in v.get("aliases", [])]
    if len(abbrev_models) == 1:
        return abbrev_models[0]
    if model not in MODELS:
        logger.error("Model not found: %s\n\nAvailable models and aliases:", model)
        models(aliases=True, file=stderr)
        sys.exit(1)
    return model


class AutoInit:  # pylint: disable=too-few-public-methods
    """Classes for handling options, automatically setting attributes from kwargs"""

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)

    def __str__(self):
        attributes = []
        for key, value in vars(self).items():
            if not key.startswith("_"):
                attributes.append(f"{key}={value!r}")
        class_name = self.__class__.__name__
        return f"{class_name}({', '.join(attributes)})"

    def __copy__(self):
        """Implement shallow copy"""
        cls = self.__class__
        result = cls.__new__(cls)
        result.__dict__.update(self.__dict__)
        return result

    def __deepcopy__(self, memo):
        """Implement deep copy"""
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            setattr(result, k, deepcopy(v, memo))
        return result

    def clone(self, **kwargs):
        """Create a copy with optional overrides"""
        new_dict = self.__dict__.copy()
        new_dict.update(kwargs)
        return self.__class__(**new_dict)


class Options(AutoInit):  # pylint: disable=too-few-public-methods
    """Options for the chat function."""

    model: str = default_model
    fake: bool = False
    temperature: float | None = None
    token_limit: int | None = None
    indent: str | None = None
    timeit: bool = False
    system: str | None = None
    stop: list[str] | None = None
    repetition_penalty: float | None = None

    def __init__(self, **kwargs):
        if "model" in kwargs:
            if kwargs["model"] in ("", None):
                kwargs["model"] = default_model
            elif kwargs["model"] in ("s", "small"):
                kwargs["model"] = default_model_small
            kwargs["model"] = get_model_by_alias(kwargs["model"])
        super().__init__(**kwargs)


# Async functions for different API clients


async def achat_openai(opts: Options, messages, client=None, citations=False):
    """Chat with OpenAI ChatGPT models asynchronously."""
    if client is None:
        client = openai_async_client
    model = MODELS[opts.model]
    model_id = model["id"]

    logger.debug("model: %s", model_id)

    temperature = opts.temperature
    token_limit = opts.token_limit

    if temperature is None:
        temperature = DEFAULT_TEMPERATURE
    if token_limit is None:
        token_limit = TOKEN_LIMIT

    min_temp = model.get("temp_min", 0)
    max_temp = model.get("temp_max", OPENAI_MAX_TEMPERATURE)
    temperature = min(max(temperature, min_temp), max_temp)

    # logger.info("achat_openai: messages: %s", json.dumps(messages, indent=2))

    logger.debug("openai temperature: %r", temperature)

    options = {
        "messages": messages,
        "model": model_id,
        "temperature": temperature,
    }

    if opts.repetition_penalty is not None:
        options["repetition_penalty"] = opts.repetition_penalty

    if token_limit != inf:
        options["max_tokens"] = token_limit

    if opts.stop:
        options["stop"] = opts.stop
        if len(opts.stop) > 4:
            logger.warning("achat_openai: too many stop sequences, truncating to 4")
            options["stop"] = opts.stop[:4]

    if opts.timeit:
        start_time = time.time()

    # logger.info("options: %s", options)

    raw_response = await client.chat.completions.with_raw_response.create(**options)
    response = raw_response.parse()

    # logger.warning("raw response: %r %r", raw_response, dir(raw_response))

    if opts.timeit:
        print(f"time: {time.time() - start_time:.3f}", file=stderr)

    logger.debug("llm: response: %s", response)

    message = response.choices[0].message
    content = message.content

    # Support Perplexity citations
    try:
        cites = response.citations
    except AttributeError:
        cites = []

    if citations and cites:
        content = replace_citations(content, cites)

    output_message = {
        "role": message.role,
        "content": content,
    }

    return output_message


def replace_citations(content, cites):
    # Split content into code and non-code segments
    segments = []
    current_pos = 0

    # Find code blocks (```...```)
    code_block_matches = list(re.finditer(r"```.*?\n.*?```", content, re.DOTALL))

    # Find inline code (`...`)
    inline_code_matches = list(re.finditer(r"`[^`]+`", content))

    # Combine and sort all code segments
    all_code_segments = [(m.start(), m.end(), "block") for m in code_block_matches]
    all_code_segments.extend([(m.start(), m.end(), "inline") for m in inline_code_matches])
    all_code_segments.sort()

    # Split content into code and non-code segments
    for start, end, _ in all_code_segments:
        if start > current_pos:
            # Add non-code segment
            segments.append(("text", content[current_pos:start]))
        # Add code segment
        segments.append(("code", content[start:end]))
        current_pos = end

    # Add final non-code segment if any
    if current_pos < len(content):
        segments.append(("text", content[current_pos:]))

    # Find existing citations only in non-code segments
    existing_citations = set()
    for segment_type, segment_content in segments:
        if segment_type == "text":
            existing_citations.update(int(m[1]) for m in re.finditer(r"\[(\d+)\]", segment_content))

    def citation_escape(url):
        return url.replace("(", "%28").replace(")", "%29")

    # Process each segment
    result = []
    for segment_type, segment_content in segments:
        if segment_type == "code":
            # Leave code segments unchanged
            result.append(segment_content)
        else:
            # Replace citations in non-code segments
            processed_content = segment_content
            for i, citation in enumerate(cites, 1):
                escaped = citation_escape(citation)
                if i in existing_citations:
                    processed_content = re.sub(rf"\[{i}\]", f"[[{i}]]({escaped})", processed_content)
            result.append(processed_content)

    content = "".join(result)

    # Add unused citations at the end
    unused_citations = []
    for i, citation in enumerate(cites, 1):
        if i not in existing_citations:
            escaped = citation_escape(citation)
            unused_citations.append(f"[[{i}]]({escaped})")
    if unused_citations:
        content += "\n\nAdditional citations: " + " ".join(unused_citations)

    return content


async def achat_perplexity(opts: Options, messages):
    """Chat with Perplexity models asynchronously."""
    return await achat_openai(opts, messages, client=perplexity_async_client, citations=True)


async def achat_xai(opts: Options, messages):
    """Chat with xAI models asynchronously."""
    return await achat_openai(opts, messages, client=xai_async_client)


async def achat_deepseek(opts: Options, messages):
    """Chat with Deepseek models asynchronously."""
    return await achat_openai(opts, messages, client=deepseek_async_client)


async def achat_openrouter(opts: Options, messages):
    """Chat with OpenRouter models asynchronously."""
    return await achat_openai(opts, messages, client=openrouter_async_client)


async def achat_claude(opts: Options, messages):
    """Chat with Anthropic Claude models asynchronously."""
    model = MODELS[opts.model]
    model_id = model["id"]

    temperature = opts.temperature
    token_limit = opts.token_limit

    if temperature is None:
        temperature = DEFAULT_TEMPERATURE
    if token_limit is None:
        token_limit = TOKEN_LIMIT

    min_temp = model.get("temp_min", 0)
    max_temp = model.get("temp_max", CLAUDE_MAX_TEMPERATURE)
    temperature = min(max(temperature, min_temp), max_temp)

    logger.debug("claude temperature: %r", temperature)

    options = {
        "model": model_id,
        "temperature": temperature,
    }

    if token_limit != inf:
        options["token_limit"] = token_limit

    if opts.stop:
        options["stop_sequences"] = opts.stop

    if opts.timeit:
        start_time = time.time()

    # support system message in the first message
    if messages[0]["role"] == "system":
        options["system"] = messages[0]["content"]
        messages = messages[1:]

    # logger.info("achat_claude: messages: %s", json.dumps(messages, indent=2))

    response = await claude.chat_claude(messages, _async=True, **options)

    if opts.timeit:
        print(f"time: {time.time() - start_time:.3f}", file=stderr)

    completion = claude.response_completion(response)
    message = {"role": "assistant", "content": completion}
    return message


async def achat_google(opts: Options, messages):
    """Chat with Google models asynchronously."""
    model = MODELS[opts.model]
    model_id = model["id"]

    api_key_name = model.get("api_key", "GOOGLE_API_KEY")
    if api_key_name == "GOOGLE_API_KEY":
        client = google_client
    else:
        api_key = os.environ.get(api_key_name)
        client = google_genai.Client(api_key=api_key)

    temperature = opts.temperature
    token_limit = opts.token_limit

    if temperature is None:
        temperature = DEFAULT_TEMPERATURE
    if token_limit is None:
        token_limit = TOKEN_LIMIT

    min_temp = model.get("temp_min", 0)
    max_temp = model.get("temp_max", GOOGLE_MAX_TEMPERATURE)
    temperature = min(max(temperature, min_temp), max_temp)

    logger.debug("google temperature: %r", temperature)

    options = {
        "temperature": temperature,
    }

    if token_limit != inf:
        options["max_output_tokens"] = token_limit

    if opts.stop:
        options["stop_sequences"] = opts.stop
        if len(opts.stop) > 5:
            logger.warning("achat_google: too many stop sequences, truncating to 5")
            options["stop_sequences"] = opts.stop[:5]

    # generation_config: generation_types.GenerationConfigType

    history = []

    types = google_genai.types

    # logger.info("google messages: %r", messages)

    if messages and messages[0]["role"] == "system":
        options["system_instruction"] = messages[0]["content"]
        messages.pop(0)

    # squash_messages = False  # dumb new API might need it?! :[

    for msg in messages:
        role = msg["role"]
        if role == "system":
            role = "user"
            msg["content"] = f"System: {msg['content']}"
        elif role != "user":
            role = "model"

        # if squash_messages and history and role == history[-1].role:
        #     history[-1].parts[0].text += "\n\n" + msg["content"]
        # else:

        # is content a list?
        parts = msg["content"] if isinstance(msg["content"], list) else [msg["content"]]

        for i in range(len(parts)):
            if isinstance(parts[i], str):
                parts[i] = types.Part(text=parts[i])
            if isinstance(parts[i], dict) and parts[i]["type"] == "text":
                parts[i] = types.Part(text=parts[i]["text"])
            elif not isinstance(parts[i], types.Part):
                raise ValueError(f"achat_google: invalid part type: {type(parts[i])}")

        history.append(types.Content(role = role, parts = parts))

    # history = [{'role': 'user', 'parts': ['System: You are Flashi. Please only reply with a single message, as Flashi; do not impersonate other characters!']}]

    config = types.GenerateContentConfig(
#        top_k=2,
#        top_p=0.5,
#        response_mime_type='application/json',
#        seed=42,
        **options,
    )

    # logger.info("google config: %r", config)

    # logger.info("history: %r", history)

    if opts.timeit:
        start_time = time.time()

    response = await client.aio.models.generate_content(model=model_id, contents=history, config=config)

    if opts.timeit:
        print(f"time: {time.time() - start_time:.3f}", file=stderr)

    output_message = {
        "role": "assistant",
        "content": response.text,
    }

    return output_message


async def allm_chat(opts: Options, messages):
    """Send a list of messages to the model, and return the response asynchronously. This is the core function used by everything else."""
    logger.debug("llm_chat: input: %r", messages)

    opts = opts.clone()

    if opts.system is not None:
        system_message_obj = {"role": "system", "content": opts.system}
        logger.warning("system message: %s", system_message_obj)
        messages = [system_message_obj] + messages

    model = MODELS[opts.model]
    vendor = model["vendor"]

    if model.get("vision", False):
        logger.debug("llm_chat: vision, trying to format messages")
        messages = [llm_vision.format_message_for_vision(message, vendor) for message in messages]
        logger.debug("llm_chat: vision messages: %r", [msg for msg in messages if "image" in msg["content"] or "image_url" in msg["content"]])
    else:
        messages = [llm_vision.remove_images_from_message(message) for message in messages]

    if model.get("no_stop") or vendor == "perplexity":
        opts.stop = None

    if opts.fake:
        return fake_completion
    if vendor == "anthropic":
        return await achat_claude(opts, messages)
    if vendor == "openai":
        return await achat_openai(opts, messages)
    if vendor == "perplexity":
        return await achat_perplexity(opts, messages)
    if vendor == "google":
        return await achat_google(opts, messages)
    if vendor == "xai":
        return await achat_xai(opts, messages)
    if vendor == "deepseek":
        return await achat_deepseek(opts, messages)
    if vendor == "openrouter":
        return await achat_openrouter(opts, messages)
    raise ValueError(f"unknown model: {model}")


def split_message_line(message, allowed_roles=None):
    """Split a message into a role and content."""

    try:
        role, message = message.split(":", 1)
    except ValueError as ex:
        raise ValueError(f"invalid message, missing role: {message}") from ex

    if allowed_roles is not None and role not in allowed_roles:
        raise ValueError(f"invalid role in message: {role}")

    message = message.strip()

    return role, message


def lines_to_messages(lines):
    """Convert a list of lines to a list of messages, with roles."""

    messages = []

    # add the input messages
    i = 0
    line = lines[0]
    while i < len(lines):
        role, message = split_message_line(line, allowed_roles=ALLOWED_ROLES)
        while True:
            i += 1
            if i == len(lines):
                break
            line = lines[i].rstrip("\r\n")
            if line and not re.match(r"^\s", line):
                break
            line = re.sub(r"^\s", "", line)
            message += "\n" + line

        message_obj = {"role": role, "content": message}
        logger.debug("input message: %s", message_obj)
        messages.append(message_obj)

        # the role alternates by default
        role = "assistant" if role == "user" else "user"

    return messages


def messages_to_lines(messages):
    """Convert a list of messages to a list of lines, with roles."""
    lines = []
    # add the output messages

    for message in messages:
        role = message["role"]
        content = message["content"].strip()
        content = re.sub(r"\n", "\n\t", content)
        line = f"{role}:\t{content}\n"
        lines.append(line)
    return lines


def read_utf_replace(istream):
    """Read input, replacing invalid UTF-8 with the replacement character."""
    try:
        input_data = istream.buffer.read()
        input_text = input_data.decode("utf-8", errors="replace")
    except UnicodeDecodeError as ex:
        logger.warning("error reading input: %s", ex)
        input_text = istream.read()
    return input_text


# Async functions for processing and querying


async def aprocess(
    *prompt,
    prompt2: str | None = None,
    istream: IO[str] = None,
    ostream: IO[str] = None,
    model: str = default_model,
    indent=None,
    temperature=None,
    token_limit=None,
    retries=RETRIES,
    empty_ok=False,
    empty_to_empty=True,
    log=True,
    lines=False,
    repeat=False,
    get_json=False,
    timeit=False,
    system=None,
    stop=None,
):
    """Process some text through the LLM with a prompt asynchronously."""
    if __name__ == "__main__":
        istream = stdin
        ostream = stdout

    prompt_str = " ".join(prompt)
    prompt_str = prompt_str.rstrip()

    input_text = read_utf_replace(istream)
    input_text = input_text.rstrip()

    if empty_ok:
        empty_to_empty = False
    if not input_text and empty_to_empty:
        return ""
    if not input_text and not empty_ok:
        raise ValueError("no input")

    if prompt2:
        prompt2 = prompt2.rstrip()
    if repeat:
        prompt2 = re.sub(r"\bbelow\b", "above", prompt_str)

    if not lines:
        return await aprocess2(
            prompt_str,
            prompt2,
            input_text,
            ostream=ostream,
            model=model,
            indent=indent,
            temperature=temperature,
            token_limit=token_limit,
            retries=retries,
            log=log,
            get_json=get_json,
            system=system,
            stop=stop,
        )

    # split the input into lines
    lines = input_text.splitlines()
    output = []

    for line in lines:
        line = line.rstrip()
        if not line:
            continue
        output1 = await aprocess2(
            prompt_str,
            prompt2,
            line,
            ostream=ostream,
            model=model,
            indent=indent,
            temperature=temperature,
            token_limit=token_limit,
            retries=retries,
            log=log,
            get_json=get_json,
            system=system,
            stop=stop,
        )
        output.append(output1)

    output_s = "\n".join(output)

    return output_s


async def aprocess2(prompt, prompt2, input_text, ostream, model, indent, temperature, token_limit, retries, log, get_json, system, stop):
    """Process some text through the LLM with a prompt asynchronously."""
    full_input = f"""
{prompt}

{input_text}
"""
    if prompt2:
        full_input += "\n" + prompt2 + "\n"
    return await aquery(
        full_input,
        ostream=ostream,
        model=model,
        indent=indent,
        temperature=temperature,
        token_limit=token_limit,
        retries=retries,
        log=log,
        get_json=get_json,
        system=system,
        stop=stop,
    )


async def aquery(
    *prompt,
    ostream: IO[str] | None = None,
    model: str = default_model,
    indent=None,
    temperature=None,
    token_limit=None,
    retries=RETRIES,
    log=True,
    get_json=False,
    timeit=False,
    system=None,
    stop=None,
):
    """Ask the LLM a question asynchronously."""
    if __name__ == "__main__":
        ostream = stdout
    opts = Options(**vars())
    return await aretry(aquery2, retries, opts, *prompt, ostream=ostream, log=log, get_json=get_json)


async def aquery2(opts: Options, *prompt, ostream: IO[str] | None = None, log=True, get_json=False):
    """Ask the LLM a question asynchronously."""
    prompt = " ".join(prompt)
    prompt = prompt.rstrip() + "\n"

    input_message = {"role": "user", "content": prompt}
    output_message = await allm_chat(opts, [input_message])
    content = output_message["content"]

    # log the input and empty output file
    if log:
        LOGDIR.mkdir(parents=True, exist_ok=True)
        assert len("answer") == len("prompt")  # better be sure!
        max_len = LOGFILE_NAME_MAX_LEN - len("19760101-000000.answer..md")
        basename = slug(prompt)[:max_len]
        while True:
            time_s = time.strftime("%Y%m%d-%H%M%S")
            logfile = LOGDIR / f"{time_s}.answer.{basename}.md"
            logfile_prompt = LOGDIR / Path(f"{time_s}.prompt.{basename}.md")
            if not logfile.exists() and not logfile_prompt.exists():
                break
            time.sleep(0.1)
        logfile_prompt.write_text(prompt.rstrip() + "\n", encoding="utf-8")
        logfile.write_text("", encoding="utf-8")

    # fix indentation for code
    if opts.indent:
        logger.warning("fix indentation for code")
        lines = content.splitlines()
        lines = tab.fix_indentation_list(lines, opts.indent)
        content = "".join(lines)

    # log the output
    if log:
        logfile.write_text(content.rstrip() + "\n", encoding="utf-8")

    if get_json:
        try:
            content = json.loads(content)
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON response")

    if ostream:
        if isinstance(content, dict):
            json.dump(content, ostream, indent=2)
        else:
            print(content, file=ostream)
        return ""

    return content


# TODO use backoff module?
async def aretry(fn, n_tries, *args, sleep_min=1, sleep_max=2, **kwargs):
    """Retry an async function n_tries times."""
    for i in range(n_tries):
        try:
            return await fn(*args, **kwargs)
        except Exception as ex:  # pylint: disable=broad-except
            if str(type(ex)) not in exceptions_to_retry:
                raise ex
            delay = random.uniform(sleep_min, sleep_max)
            logger.warning("retry: exception, sleeping for %.3f: %s", delay, ex)
            msg = str(ex)
            if i == n_tries - 1:
                raise ex
            await asyncio.sleep(delay)
            sleep_min *= 2
            sleep_max *= 2
    return None


async def achat(
    istream=stdin, ostream=stdout, model=default_model, fake=False, temperature=None, token_limit=None, retries=RETRIES, system=None, stop=None
):
    """Chat with the LLM asynchronously."""
    opts = Options(**vars())
    return await aretry(achat2, retries, opts, istream=istream, ostream=ostream)


async def achat2(opts: Options, istream=stdin, ostream=stdout):
    """Chat with the LLM asynchronously."""
    input_lines = read_utf_replace(istream).splitlines()
    input_messages = lines_to_messages(input_lines)
    response_message = await allm_chat(opts, input_messages)
    output_lines = messages_to_lines([response_message])
    ostream.writelines(output_lines)


# Synchronous wrappers for async functions
# TODO we can just use async functions directly with ally.main.run now
@arg("-m", "--model", default=default_model, help="model name")
@arg("-f", "--fake", action="store_true", help="return fake completions")
@arg("-t", "--temperature", type=float, help="temperature")
@arg("-n", "--token-limit", type=int, help="token limit")
@arg("-r", "--retries", type=int, default=RETRIES, help="number of retries")
@arg("-s", "--system", help="system prompt")
@arg("-S", "--stop", nargs="*", help="stop sequences")
def chat(istream=stdin, ostream=stdout, model=default_model, fake=False, temperature=None, token_limit=None, retries=RETRIES, system=None, stop=None):
    """Synchronous wrapper for achat."""
    return asyncio.run(achat(istream, ostream, model, fake, temperature, token_limit, retries, system=system, stop=stop))


@arg("prompt", nargs="+", help="prompt text")
@arg("-o", "--output", dest="ostream", default=None, help="output file")
@arg("-m", "--model", default=default_model, help="model name")
@arg("-I", "--indent", default=None, help="indentation string")
@arg("-t", "--temperature", type=float, help="temperature")
@arg("-n", "--token-limit", type=int, help="token limit")
@arg("-r", "--retries", type=int, default=RETRIES, help="number of retries")
@arg("-l", "--log", action="store_true", help=f"log to a file in {LOGDIR}")
@arg("-j", "--json", action="store_true", help="output JSON", dest="get_json")
@arg("-T", "--timeit", action="store_true", help="time the actual request")
@arg("-s", "--system", help="system prompt")
@arg("-S", "--stop", nargs="*", help="stop sequences")
def query(
    *prompt,
    ostream: IO[str] | None = None,
    model: str = default_model,
    indent=None,
    temperature=None,
    token_limit=None,
    retries=RETRIES,
    log=True,
    get_json=False,
    timeit=False,
    system=None,
    stop=None,
):
    """Synchronous wrapper for aquery."""
    return asyncio.run(
        aquery(
            *prompt,
            ostream=ostream,
            model=model,
            indent=indent,
            temperature=temperature,
            token_limit=token_limit,
            retries=retries,
            log=log,
            get_json=get_json,
            timeit=timeit,
            system=system,
            stop=stop,
        )
    )


@arg("prompt", nargs="+", help="prompt text")
@arg("-P", "--prompt2", help="second prompt text")
@arg("-i", "--input", dest="istream", default=None, help="input file")
@arg("-o", "--output", dest="ostream", default=None, help="output file")
@arg("-m", "--model", default=default_model, help="model name")
@arg("-I", "--indent", default=None, help="indentation string")
@arg("-t", "--temperature", type=float, help="temperature")
@arg("-n", "--token-limit", type=int, help="token limit")
@arg("-r", "--retries", type=int, default=RETRIES, help="number of retries")
@arg("-e", "--empty-to-empty", action="store_true", help="return empty string for empty input")
@arg("-E", "--empty-ok", action="store_true", help="allow empty input")
@arg("-l", "--log", action="store_true", help=f"log to a file in {LOGDIR}")
@arg("-x", "--lines", action="store_true", help="process each line separately, like perl -p")
@arg("-R", "--repeat", action="store_true", help="repeat the prompt as prompt2, changing 'below' to 'above' only")
@arg("-j", "--json", action="store_true", help="output JSON", dest="get_json")
@arg("-T", "--timeit", action="store_true", help="time the actual request")
@arg("-s", "--system", help="system prompt")
@arg("-S", "--stop", nargs="*", help="stop sequences")
def process(
    *prompt,
    prompt2: str | None = None,
    istream: IO[str] | None = None,
    ostream: IO[str] | None = None,
    model: str = default_model,
    indent=None,
    temperature=None,
    token_limit=None,
    retries=RETRIES,
    empty_ok=False,
    empty_to_empty=True,
    log=True,
    lines=False,
    repeat=False,
    get_json=False,
    timeit=False,
    system=None,
    stop=None,
):
    """Synchronous wrapper for aprocess."""
    return asyncio.run(
        aprocess(
            *prompt,
            prompt2=prompt2,
            istream=istream,
            ostream=ostream,
            model=model,
            indent=indent,
            temperature=temperature,
            token_limit=token_limit,
            retries=retries,
            empty_ok=empty_ok,
            empty_to_empty=empty_to_empty,
            log=log,
            lines=lines,
            repeat=repeat,
            get_json=get_json,
            timeit=timeit,
            system=system,
            stop=stop,
        )
    )


def decimal_string(num: float, places=6) -> str:
    """Convert a float to a string without scientific notation."""
    return f"{num:.{places}f}".rstrip("0").rstrip(".")


@arg("-m", "--model", default=default_model, help="model name")
@arg("-I", "--in-cost", action="store_true", help="show input cost")
@arg("-O", "--out-cost", action="store_true", help="show output cost")
def count(istream=stdin, model=default_model, in_cost=False, out_cost=False):
    """count tokens in input"""
    opts = Options(**vars())
    text = read_utf_replace(istream)
    model = MODELS[opts.model]
    vendor = model["vendor"]
    if vendor == "openai":
        try:
            enc = tiktoken.encoding_for_model(opts.model)
        except KeyError:
            enc_name = "o200k_base"
            logger.warning("model %s not known to tiktoken, assuming %s", opts.model, enc_name)
            enc = tiktoken.get_encoding(enc_name)
        tokens = enc.encode(text)
        n_tokens = len(tokens)
    elif vendor == "anthropic":
        n_tokens = claude.count(text, model=model["id"])
    elif vendor == "perplexity":
        tokens = get_llama3_tokenizer().tokenize(text)
        n_tokens = len(tokens)
    elif vendor == "google":
        try:
            tokenizer = google_tokenization.get_tokenizer_for_model(opts.model)
        except ValueError as ex:
            if "latest" in opts.model:
                similar_model_id = opts.model.replace("-latest", "-001")
            elif opts.model.startswith("gemini-"):
                similar_model_id = "gemini-1.5-flash-002"
            else:
                raise ex
            tokenizer = google_tokenization.get_tokenizer_for_model(similar_model_id)
        n_tokens = tokenizer.count_tokens(text).total_tokens
    else:
        raise ValueError(f"unsupported model vendor for token counting: {vendor}")
    rv = [n_tokens]
    if in_cost:
        rv.append(decimal_string(model["cost_in"] * n_tokens / 1e6))
    if out_cost:
        rv.append(decimal_string(model["cost_out"] * n_tokens / 1e6))
    if (in_cost or out_cost) and "cost_req" in model:
        rv.append(decimal_string(model["cost_req"] / 1e3))
    return tuple(rv)


@arg("-A", "--no-aliases", dest="aliases", action="store_false", help="show aliases")
def models(detail=False, aliases=True, file=stdout):
    """List the available models."""

    with io.StringIO() as buffer:
        for name, model in MODELS.items():
            print(name, end="", file=buffer)
            if aliases and not detail:
                print("\t" + "\t".join(model.get("aliases", [])), end="", file=buffer)
            print(file=buffer)

            if detail:
                for k, v in model.items():
                    if k == "description":
                        v = textwrap.fill(v, width=80)
                        v = "\t \t".join(v.splitlines())
                    elif k == "aliases":
                        v = ", ".join(v)
                    print(f"\t{k}:\t{v}", file=buffer)
                print(file=buffer)

        if titty.is_tty(sys.stdout):
            buffer.seek(0)
            with io.StringIO() as output:
                tsv2txt.tsv2txt(istream=buffer, ostream=output, multi_table=True)
                print(output.getvalue(), end="")
        else:
            print(buffer.getvalue(), end="")


if __name__ == "__main__":
    main.run([chat, query, process, count, models], warn_deprecated=False)
else:
    # Load all modules in the background after a short delay
    lazy(0.1)

# TODO create compatible libraries for other APIs in future
# TODO consider splitting off the OpenAI specific stuff into a separate library
# IDEA use cached responses if possible?
