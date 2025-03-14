#!/usr/bin/env python3-allemande

# pyq: process python object notation like jq, using jq
# also supports json, xml, yaml, csv, tsv, and rfc 2822 email-style headers

# TODO: support more formats like shell env, ini, etc

import argparse
import csv
import datetime  # for evaluating .py data  # pylint: disable=unused-import
import json
import pprint
import subprocess
from email.parser import Parser
from io import StringIO
import sys
import re

import jq
import xmltodict
import ruamel.yaml
from deepmerge import always_merger

import csv_tidy
from records import read_records, write_records

which_jq = "system"  # "system" or "python"

def yaml_str_presenter(dumper, data):
    """
    Presenter for strings that detects multi-line strings and formats them 
    using the literal style (|) indicator
    """
    if re.search(r".\n.", data, flags=re.DOTALL):
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

def merge_data(data_list: list[object]) -> object:
    """Merge multiple data inputs using always_merger."""
    if not data_list:
        return None
    result = data_list[0]
    for data in data_list[1:]:
        result = always_merger.merge(result, data)
    return result


def process_input(input_file, opts) -> object:
    """Process a single input file using the appropriate loader."""
    loader = loaders[opts.from_]
    return loader(input_file, opts)


def pyq_subprocess(data, *args):
    if args == (".",):
        return data
    print(args)
    proc = subprocess.Popen(
        ["jq"] + list(args), stdin=subprocess.PIPE, stdout=subprocess.PIPE
    )
    proc.stdin.write(json.dumps(data).encode("utf-8"))
    proc.stdin.close()
    proc.wait()
    if proc.returncode:
        raise subprocess.CalledProcessError(proc.returncode, ["jq"] + list(args))
    jqout = json.loads(proc.stdout.read().decode("utf-8"))
    return jqout


def pyq_subprocess_to_file(data, out_file, *args):
    proc = subprocess.Popen(
        ["jq"] + list(args), stdin=subprocess.PIPE, stdout=out_file
    )
    proc.stdin.write(json.dumps(data).encode("utf-8"))
    proc.stdin.close()
    proc.wait()
    if proc.returncode:
        raise subprocess.CalledProcessError(proc.returncode, ["jq"] + list(args))


def pyq_jq(data, jq_program):
    p = jq.compile(jq_program)
    jqout = p.input(data).all()
    return jqout


def pyq(data, jq_program, jq_opts=None):
    if which_jq == "system":
        return pyq_subprocess(data, jq_program, *jq_opts)
    elif jq_opts:
        raise ValueError("jq_opts not supported with python jq")
    else:
        return pyq_jq(data, jq_program)


def pyq_streams(input_files: list[str], out_file, jq_program: str, opts):
    """Process input files and run jq on merged result."""
    jq_opts = opts.jq_opts or []

    # Collect data from all input files
    data_list = []
    if not input_files:
        input_files = ["-"]
    for filename in input_files:
        if filename == "-":
            data = process_input(sys.stdin, opts)
        else:
            with open(filename, encoding="utf-8") as f:
                data = process_input(f, opts)
        data_list.append(data)

    # Merge all inputs
    data = merge_data(data_list)

    formatter = formatters[opts.to]

    if opts.to == "json" and which_jq == "system":
        # we can output directly to the file,
        # which can give colorized output
        pyq_subprocess_to_file(data, out_file, jq_program, *jq_opts)
        return

    jqout = pyq(data, jq_program, jq_opts)
    output = formatter(jqout, opts)
    if output and output[-1] != "\n":
        output += "\n"
    print(output, end="", file=out_file)


def load_json(in_file, opts) -> object:
    return json.load(in_file)


def format_json(obj, opts) -> str:
    if not opts.compact:
        return json.dumps(obj, indent=4)
    return json.dumps(obj)


def load_python(in_file, opts) -> object:
    # Danger, will robinson!
    return eval(in_file.read())


def format_python(obj, opts) -> str:
    if not opts.compact:
        return pprint.pformat(obj, indent=4)
    return repr(obj)


def load_xml(in_file, opts) -> object:
    return xmltodict.parse(in_file.read())


def format_xml(obj, opts) -> str:
    if not isinstance(obj, dict):
        obj = {"root": {"item": obj}}
    elif len(obj) > 1:
        obj = {"root": obj}
    return xmltodict.unparse(obj, pretty=not opts.compact)


def load_yaml(in_file, opts) -> object:
    yaml = ruamel.yaml.YAML(pure=True)
    return yaml.load(in_file)


def format_yaml(obj, opts) -> str:
    yaml = ruamel.yaml.YAML(pure=True)
    if not opts.compact:
        yaml.default_flow_style = False
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.representer.add_representer(str, yaml_str_presenter)
    stream = StringIO()
    yaml.dump(obj, stream)
    return stream.getvalue()


def load_csv(in_file, opts) -> object:
    reader = csv_tidy.reader(in_file, delimiter=opts.delimiter)
    headers = next(reader)
    return [dict(zip(headers, row)) for row in reader]


def format_csv(obj, opts) -> str:
    if not obj:
        return ""
    if not isinstance(obj, list):
        obj = [obj]

    output = StringIO()
    writer = csv.writer(output, delimiter=opts.delimiter)

    if isinstance(obj[0], dict):
        headers = list(obj[0].keys())
        writer.writerow(headers)
        for row in obj:
            writer.writerow(row.get(h, "") for h in headers)
    else:
        writer.writerows(obj)

    return output.getvalue()


def load_tsv(in_file, opts) -> object:
    opts.delimiter = "\t"
    return load_csv(in_file, opts)


def format_tsv(obj, opts) -> str:
    opts.delimiter = "\t"
    return format_csv(obj, opts)


def load_headers(in_file, opts) -> list[dict[str, str]]:
    parser = Parser()
    headers_list = []
    current_headers = []

    for line in in_file:
        if line.strip() == "":
            if current_headers:
                msg = parser.parsestr("\n".join(current_headers))
                headers_list.append(dict(msg.items()))
                current_headers = []
        else:
            current_headers.append(line.rstrip())

    # Don't forget the last record if it's not followed by a blank line
    if current_headers:
        msg = parser.parsestr("\n".join(current_headers))
        headers_list.append(dict(msg.items()))

    return headers_list


def format_headers(obj_list, opts) -> str:
    if not isinstance(obj_list, list):
        raise ValueError("Email headers must be a list of dictionaries")

    formatted_blocks = []
    for obj in obj_list:
        if not isinstance(obj, dict):
            raise ValueError("Each item in the list must be a dictionary")
        formatted_blocks.append("\n".join(f"{k}: {v}" for k, v in obj.items()))

    return "\n\n".join(formatted_blocks) + "\n"


def load_records(in_file, opts) -> object:
    records, _ = read_records(in_file)
    return records


def format_records(obj, opts) -> str:
    if not isinstance(obj, list):
        obj = [obj]
    output = StringIO()
    write_records(output, obj)
    return output.getvalue()


loaders = {
    "json": load_json,
    "py": load_python,
    "xml": load_xml,
    "yaml": load_yaml,
    "csv": load_csv,
    "tsv": load_tsv,
    "headers": load_headers,
    "records": load_records,
}


formatters = {
    "json": format_json,
    "py": format_python,
    "xml": format_xml,
    "yaml": format_yaml,
    "csv": format_csv,
    "tsv": format_tsv,
    "headers": format_headers,
    "records": format_records,
}


def main():
    """Process input files with jq-like functionality."""
    parser = argparse.ArgumentParser(
        description="Process python object notation like jq, using jq"
    )

    parser.add_argument(
        "--from",
        "-f",
        dest="from_",
        default="py",
        choices=formatters.keys(),
        help="input format",
    )
    parser.add_argument(
        "--to",
        "-t",
        dest="to",
        default="json",
        choices=formatters.keys(),
        help="output format",
    )
    parser.add_argument(
        "--format",
        "-F",
        dest="format",
        default=None,
        choices=formatters.keys(),
        help="input and output format",
    )
    parser.add_argument(
        "--compact", "-c", action="store_true", help="compact output"
    )
    parser.add_argument("--delimiter", "-d", default=",", help="CSV delimiter")
    parser.add_argument(
        "--jq", choices=("system", "python"), help="use system jq or python jq"
    )
    parser.add_argument(
        "--input", "-i", nargs="+", help="input files (use - for stdin)"
    )
    parser.add_argument("jq_program", nargs="?", help="jq program")
    parser.add_argument("jq_opts", nargs=argparse.REMAINDER, help="jq options")

    opts = parser.parse_args()

    if opts.format is not None:
        opts.from_ = opts.format
        opts.to = opts.format

    if not opts.jq_program:
        opts.jq_program = "."

    if opts.jq:
        global which_jq  # pylint: disable=global-statement
        which_jq = opts.jq

    pyq_streams(opts.input, sys.stdout, opts.jq_program, opts)


if __name__ == "__main__":
    main()
