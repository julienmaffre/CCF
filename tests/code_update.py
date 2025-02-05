# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the Apache 2.0 License.
import e2e_args
import infra.ccf
import infra.proc
import json
import logging
import os
import subprocess
import sys
import time
from loguru import logger as LOG


def get_code_id(lib_path):
    oed = subprocess.run(
        [args.oesign, "dump", "-e", lib_path], capture_output=True, check=True
    )
    lines = [
        line
        for line in oed.stdout.decode().split(os.linesep)
        if line.startswith("mrenclave=")
    ]

    return lines[0].split("=")[1]


def add_new_code(network, new_code_id):
    LOG.debug(f"Adding new code id: {new_code_id}")

    primary, term = network.find_primary()
    result = network.consortium.propose(
        1, primary, None, None, "add_code", f"--new-code-id={new_code_id}"
    )

    network.consortium.vote_using_majority(primary, result[1]["id"])


def run(args):
    hosts = ["localhost", "localhost"]

    with infra.ccf.network(
        hosts, args.build_dir, args.debug_nodes, args.perf_nodes, pdb=args.pdb
    ) as network:
        network.start_and_join(args)
        primary, others = network.find_nodes()

        LOG.info("Adding a new node")
        new_node = network.create_and_trust_node(args.package, "localhost", args)
        assert new_node

        new_code_id = get_code_id(f"{args.patched_file_name}.so.signed")

        LOG.info(f"Adding a node with unsupported code id {new_code_id}")
        assert (
            network.create_and_trust_node(args.patched_file_name, "localhost", args)
            == None
        ), "Adding node with unsupported code id should fail"

        add_new_code(network, new_code_id)

        new_nodes = set()
        old_nodes_count = len(network.nodes)
        new_nodes_count = old_nodes_count + 1

        LOG.info(
            f"Adding more new nodes ({new_nodes_count}) than originally existed ({old_nodes_count})"
        )
        for _ in range(0, new_nodes_count):
            new_node = network.create_and_trust_node(
                args.patched_file_name, "localhost", args
            )
            assert new_node
            new_nodes.add(new_node)

        for node in new_nodes:
            new_primary = node
            break

        LOG.info("Stopping all original nodes")
        old_nodes = set(network.nodes).difference(new_nodes)
        for node in old_nodes:
            LOG.debug(f"Stopping old node {node.node_id}")
            node.stop()

        LOG.info("Waiting for a new primary to be elected...")
        time.sleep(args.election_timeout * 6 / 1000)

        new_primary, _ = network.find_primary()
        LOG.info(f"Waited, new_primary is {new_primary.node_id}")

        LOG.info("Adding another node to the network")
        new_node = network.create_and_trust_node(
            args.patched_file_name, "localhost", args
        )
        assert new_node
        network.wait_for_node_commit_sync()


if __name__ == "__main__":

    def add(parser):
        parser.add_argument(
            "-p",
            "--package",
            help="The enclave package to load (e.g., libsimplebank)",
            default="libloggingenc",
        )
        parser.add_argument(
            "--oesign", help="Path to oesign binary", type=str, required=True
        )
        parser.add_argument(
            "--oeconfpath",
            help="Path to oe configuration file",
            type=str,
            required=True,
        )
        parser.add_argument(
            "--oesignkeypath", help="Path to oesign key", type=str, required=True
        )

    args = e2e_args.cli_args(add)
    if args.enclave_type != "debug":
        LOG.warning("Skipping code update test with virtual enclave")
        sys.exit()

    args.package = args.app_script and "libluagenericenc" or "libloggingenc"
    args.patched_file_name = "{}.patched".format(args.package)
    run(args)
