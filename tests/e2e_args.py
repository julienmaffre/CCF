# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the Apache 2.0 License.
import argparse
import os
import infra.path
import sys


def cli_args(add=lambda x: None, parser=None, accept_unknown=False):
    if parser is None:
        parser = argparse.ArgumentParser(
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
    parser.add_argument("-b", "--build-dir", help="Build directory", default=".")
    parser.add_argument(
        "-d",
        "--debug-nodes",
        help="List of node ids. Nodes that are specified will need to be started manually",
        action="append",
        default=[],
    )
    parser.add_argument(
        "--perf-nodes",
        help="List of node ids. Nodes that should be run under perf, capturing performance data",
        action="append",
        default=[],
    )
    parser.add_argument(
        "-e",
        "--enclave-type",
        help="Enclave type",
        default=os.getenv("TEST_ENCLAVE", "debug"),
        choices=("debug", "virtual"),
    )
    parser.add_argument(
        "-l",
        "--host-log-level",
        help="Runtime host log level",
        default="info",
        choices=("trace", "debug", "info", "fail", "fatal"),
    )
    parser.add_argument(
        "--json-log-path",
        help="Path to directory where the json logger output will be sent to. \
        The json logs will be dumped into a file named <json_log_path>/{label}_{node_id}",
        default=os.getenv("JSON_LOG_PATH", None),
    )
    parser.add_argument(
        "-g",
        "--gov-script",
        help="Path to governance script",
        default="../src/runtime_config/gov.lua",
    )
    parser.add_argument("-s", "--app-script", help="Path to app script")
    parser.add_argument(
        "--ignore-quote",
        help="Ignore node quote (e.g. virtual enclave)",
        action="store_true",
    )
    parser.add_argument(
        "-o",
        "--network-only",
        help="Only start the network, do not run the client, and wait.",
        action="store_true",
    )
    parser.add_argument(
        "--sig-max-tx", help="Max transactions between signatures", type=int
    )
    parser.add_argument(
        "--sig-max-ms", help="Max milliseconds between signatures", type=int
    )
    parser.add_argument(
        "--memory-reserve-startup",
        help="Reserve this many bytes of memory on startup, to simulate memory restrictions",
        type=int,
    )
    parser.add_argument(
        "--wait-with-client",
        help="If set, the python client is used to query joining nodes",
        action="store_true",
    )
    parser.add_argument(
        "--election-timeout",
        help="Maximum election timeout for each node in the network",
        type=int,
        default=100000,
    )
    parser.add_argument(
        "--pdb", help="Break to debugger on exception", action="store_true"
    )
    parser.add_argument(
        "--notify-server", help="Server host to notify progress to (host:port)"
    )
    parser.add_argument(
        "--workspace",
        help="Temporary directory where nodes store their logs, ledgers, quotes, etc.",
        default=infra.path.default_workspace(),
    )
    default_label = os.path.splitext(os.path.basename(sys.argv[0]))[0]
    parser.add_argument(
        "--label", help="Unique identifier for the test", default=default_label
    )
    parser.add_argument(
        "--enforce-reqs",
        help="Enforce test requirements (useful when running the test suite)",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--pbft", help="Opens network the PBFT way", action="store_true",
    )
    add(parser)

    if accept_unknown:
        return parser.parse_known_args()
    else:
        return parser.parse_args()
