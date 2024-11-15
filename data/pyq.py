#!/usr/bin/env python3-allemande

# pyq: process python object notation like jq, using jq
# also supports json, xml, yaml, csv, tsv, and rfc 2822 email-style headers

# TODO: support more formats like shell env, ini, etc

import sys
import json
import csv
from email.parser import Parser
import subprocess
import argparse
import pprint
import xmltodict
import yaml
import jq
from io import StringIO

from rec import read_records, write_records


which_jq = "system"  # "system" or "python"


def pyq_subprocess(data, *args):
    proc = subprocess.Popen(["jq"] + list(args), stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    proc.stdin.write(json.dumps(data).encode("utf-8"))
    proc.stdin.close()

    jqout = json.loads(proc.stdout.read().decode("utf-8"))
    return jqout


def pyq_subprocess_to_file(data, out_file, *args):
    proc = subprocess.Popen(["jq"] + list(args), stdin=subprocess.PIPE, stdout=out_file)
    proc.stdin.write(json.dumps(data).encode("utf-8"))
    proc.stdin.close()


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


def pyq_streams(in_file, out_file, jq_program, opts):
    jq_opts = opts.jq_opts or []

    loader = loaders[opts.from_]
    formatter = formatters[opts.to]

    data = loader(in_file, opts)

    if opts.to == "json" and which_jq == "system":
        # we can output directly to the file,
        # which can give colorized output
        pyq_subprocess_to_file(data, out_file, jq_program, *jq_opts)
        return

    jqout = pyq(data, jq_program, jq_opts)
    print(formatter(jqout, opts), file=out_file)


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
    return yaml.safe_load(in_file)


def format_yaml(obj, opts) -> str:
    if not opts.compact:
        return yaml.dump(obj, default_flow_style=opts.compact, indent=4)
    return yaml.dump(obj)


def load_csv(in_file, opts) -> object:
    reader = csv.reader(in_file, delimiter=opts.delimiter)
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
    parser = argparse.ArgumentParser(description="Process python object notation like jq, using jq")

    # options to read and write either python object notation or json
    # default is py to json
    # option --from to specify input format
    parser.add_argument(
        "--from", "-f", dest="from_", default="py", choices=formatters.keys(), help="input format"
    )
    # option --to to specify output format
    parser.add_argument(
        "--to", "-t", dest="to", default="json", choices=formatters.keys(), help="output format"
    )
    # option --format to specify both input and output format
    parser.add_argument(
        "--format",
        "-F",
        dest="format",
        default=None,
        choices=formatters.keys(),
        help="input and output format",
    )
    # option --ugly
    parser.add_argument("--compact", "-c", action="store_true", help="compact output")
    parser.add_argument("--delimiter", "-d", default=",", help="CSV delimiter")
    parser.add_argument("--jq", choices=("system", "python"), help="use system jq or python jq")
    parser.add_argument("jq_program", nargs="?", help="jq program")
    parser.add_argument("jq_opts", nargs=argparse.REMAINDER, help="jq options")

    opts = parser.parse_args()

    if opts.format is not None:
        opts.from_ = opts.format
        opts.to = opts.format

    if not opts.jq_program:
        opts.jq_program = "."

    if opts.jq:
        global which_jq
        which_jq = opts.jq

    pyq_streams(sys.stdin, sys.stdout, opts.jq_program, opts)


if __name__ == "__main__":
    main()
