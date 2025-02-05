# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the Apache 2.0 License.
import sys
import e2e_args
import infra.ccf
import infra.proc
import suite.test_requirements as reqs
import json

import logging
import time

from loguru import logger as LOG


def check_can_progress(node):
    with node.node_client() as mc:
        check_commit = infra.checker.Checker(mc)
        with node.node_client() as c:
            check_commit(c.rpc("mkSign", params={}), result=True)


@reqs.none
def test_add_node(network, args):
    LOG.info("Adding a valid node from primary")
    new_node = network.create_and_trust_node(args.package, "localhost", args)
    assert new_node
    return network


@reqs.at_least_2_nodes
def test_add_node_from_backup(network, args):
    LOG.info("Adding a valid node from a backup")
    backup = network.find_any_backup()
    new_node = network.create_and_trust_node(
        args.package, "localhost", args, target_node=backup
    )
    assert new_node
    return network


@reqs.none
def test_add_as_many_pending_nodes(network, args):
    # Adding as many pending nodes as current number of nodes should not
    # change the raft consensus rules (i.e. majority)
    number_new_nodes = len(network.nodes)
    LOG.info(
        f"Adding {number_new_nodes} pending nodes - consensus rules should not change"
    )

    for _ in range(number_new_nodes):
        network.create_and_add_pending_node(args.package, "localhost", args)
    check_can_progress(network.find_primary()[0])
    return network


@reqs.none
def test_add_node_untrusted_code(network, args):
    if args.enclave_type == "debug":
        LOG.info("Adding an invalid node (unknown code id)")
        assert (
            network.create_and_trust_node("libluagenericenc", "localhost", args) == None
        ), "Adding node with unknown code id should fail"
    else:
        LOG.warning("Skipping unknown code id test with virtual enclave")
    return network


@reqs.at_least_2_nodes
def test_retire_node(network, args):
    LOG.info("Retiring a backup")
    primary, _ = network.find_primary()
    backup_to_retire = network.find_any_backup()
    network.consortium.retire_node(primary, backup_to_retire)
    backup_to_retire.stop()
    return network


def run(args):
    hosts = ["localhost", "localhost"]

    with infra.ccf.network(
        hosts, args.build_dir, args.debug_nodes, args.perf_nodes, pdb=args.pdb
    ) as network:
        network.start_and_join(args)
        test_add_node_from_backup(network, args)
        test_add_as_many_pending_nodes(network, args)
        test_add_node(network, args)
        test_add_node_untrusted_code(network, args)
        test_retire_node(network, args)
        test_add_node(network, args)


if __name__ == "__main__":

    def add(parser):
        parser.add_argument(
            "-p",
            "--package",
            help="The enclave package to load (e.g., libsimplebank)",
            default="libloggingenc",
        )

    args = e2e_args.cli_args(add)
    args.package = args.app_script and "libluagenericenc" or "libloggingenc"
    run(args)
