#!/usr/bin/env python3-allemande

"""
Process OpenAPI documents into condensed markdown descriptions suitable for LLMs.
"""

import sys
from pathlib import Path
import json
import re

from ally import main, logs  # type: ignore
import yaml  # type: ignore

__version__ = "0.1.2"

logger = logs.get_logger()


def resolve_ref(schema: dict, doc: dict) -> dict:
    """Resolve a $ref schema reference."""
    if "$ref" not in schema:
        return schema

    ref_path = schema["$ref"].split("/")[1:]  # Skip initial '#'
    current = doc
    for part in ref_path:
        current = current[part]
    return current


def format_property(name: str, prop: dict, doc: dict, indent: int, prop_required: bool) -> str:
    """Format a single property."""
    if "$ref" in prop:
        prop = resolve_ref(prop, doc)

    type_str = prop.get("type", "any")
    type_hint = f":{type_str}"
    if prop_required:
        type_hint += "!"
    if "format" in prop:
        type_hint += f"({prop['format']})"
    if "enum" in prop:
        type_hint += f"[{'|'.join(str(x) for x in prop['enum'])}]"
    if "properties" in prop and type_str in ("object", "any"):
        type_hint = ""
    if type_str == "array":
        items = format_schema(prop["items"], doc, indent + 2)
        items = re.sub(r"^:", "", items)
        type_hint += "[" + items + "]"

    if "description" in prop:
        description = "\t# " + prop["description"].replace("\n", " ")
    else:
        description = ""

    value = " " + format_schema(prop, doc, indent + 2) if "properties" in prop else ""

    result = f"{' ' * indent}{name}{type_hint}{value}"

    # Add description to first line
    result = re.sub(r"$", description, result, 1, flags=re.MULTILINE)

    return result


def format_object(schema: dict, doc: dict, indent: int) -> str:
    """Format an object schema with properties."""
    props = schema.get("properties", {})
    if not props:
        return "{...}"

    required = schema.get("required", [])

    lines = []
    for name, prop in props.items():
        prop_required = name in required
        lines.append(format_property(name, prop, doc, indent, prop_required))

    return "{\n" + "\n".join(lines) + "\n" + " " * (indent - 2) + "}"


def format_schema(schema: dict, doc: dict, indent: int = 0) -> str:
    """Format a schema as a JSON-like structure with type hints."""
    if "$ref" in schema:
        schema = resolve_ref(schema, doc)

    if "type" not in schema and "properties" not in schema:
        return "{...}"

    if schema.get("type") == "array":
        items = format_schema(schema["items"], doc, indent + 2)
        items = re.sub(r"^:", "", items)
        return f"[{items}]"

    is_object = schema.get("type") == "object" or "properties" in schema

    if not is_object:
        return f":{schema.get('type', 'any')}"

    return format_object(schema, doc, indent)


def format_query_param(param: dict) -> str:
    """Format a parameter placeholder."""
    schema = param.get("schema", {})
    default = schema.get("default", "")
    type_str = schema.get("type")
    type_hint = f":{type_str}" if type_str else ""
    result = f"{param['name']}={default}{type_hint}"
    if not param["required"]:
        result = f"[{result}]"
    return result


def format_endpoint_details(path: str, method: str, details: dict, doc: dict) -> list:
    """Format details for a single endpoint."""
    output = []

    # Build the endpoint line
    params = details.get("parameters", [])
    param_str = "&".join(format_query_param(p) for p in params if p["in"] == "query")
    if param_str:
        param_str = "?" + param_str
    endpoint = f"{method.upper()} {path}{param_str}"

    # Add summary/description as heading
    summary = details.get("summary", endpoint)
    output.append(f"### {summary}\n")
    output.append(f"```\n{endpoint}")

    # Handle request body
    if "requestBody" in details:
        body_content = details["requestBody"]["content"]
        if "application/json" in body_content:
            schema = body_content["application/json"]["schema"]
            output.append(format_schema(schema, doc, 2))

    # Handle response
    if "200" in details.get("responses", {}):
        resp = details["responses"]["200"]
        if "content" in resp and "application/json" in resp["content"]:
            schema = resp["content"]["application/json"]["schema"]
            output.append("")
            output.append(format_schema(schema, doc, 2))

    output.append("```\n")

    # List error codes and descriptions, no details
    errors = [
        f"{code}: {resp.get('description', '')}"
        for code, resp in details.get("responses", {}).items()
        if code not in ["200", "default"]
    ]
    if errors:
        output.append("#### Errors\n")
        for error in errors:
            output.append(f"- {error}")
    output.append("")

    return output


def process_openapi(doc: dict) -> str:
    """Convert OpenAPI document to condensed markdown description."""
    output = []

    # Title and description
    output.append(f"# {doc.get('info', {}).get('title', 'API')}\n")
    if "description" in doc.get("info", {}):
        output.append(doc["info"]["description"])
    output.append("")

    # Server info
    if "servers" in doc:
        output.append("## Servers\n")
        for server in doc["servers"]:
            output.append(f"- {server.get('url')}")
        output.append("")

    # Security schemes
    security_schemes = doc.get("components", {}).get("securitySchemes", {})
    if security_schemes:
        output.append("## Security Schemes\n")
        yaml_output = yaml.dump(security_schemes, default_flow_style=False)
        for line in yaml_output.splitlines():
            output.append(f"  {line}")
        output.append("")

    # Endpoints
    output.append("## Endpoints\n")
    for path, methods in doc.get("paths", {}).items():
        for method, details in methods.items():
            if method == "parameters":
                continue

            endpoint_output = format_endpoint_details(path, method, details, doc)
            output.extend(endpoint_output)

    return "\n".join(output)


def condense(input_data: str) -> str:
    """Parse OpenAPI input and generate condensed markdown output."""
    try:
        doc = yaml.safe_load(input_data)
    except yaml.YAMLError:
        try:
            doc = json.loads(input_data)
        except json.JSONDecodeError as e:
            raise ValueError("Input must be valid YAML or JSON") from e

    if "openapi" not in doc:
        raise ValueError("Input does not appear to be an OpenAPI document")

    return process_openapi(doc)


def setup_args(arg):
    """Set up command-line arguments."""
    arg("files", nargs="*", help="OpenAPI files to process (default: stdin)")


def openapi_condense(files: list[str] | None = None) -> None:
    """Process OpenAPI files into condensed markdown descriptions."""
    if not files:
        input_data = sys.stdin.read()
        print(condense(input_data))
        return

    for file in files:
        input_data = Path(file).read_text(encoding="utf-8")
        if len(files) > 1:
            print(f"# Processing {file}")
        print(condense(input_data))


if __name__ == "__main__":
    main.go(openapi_condense, setup_args)
