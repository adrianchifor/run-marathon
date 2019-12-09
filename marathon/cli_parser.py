#!/usr/bin/env python3

import argparse

from marathon.version import description, version


def init_cli_parser():
    parser = argparse.ArgumentParser(prog="run", description=description)
    parser.add_argument("--version", action="version", version=version)
    subparser = parser.add_subparsers(help="commands")

    marathon_parser = subparser.add_parser("marathon", help="Deploy services to Cloud Run and setup IAM")
    marathon_parser.add_argument("--build", "-b", help="Also build containers using Cloud Build",
                                 action="store_true",
                                 default=False)

    init_parser = subparser.add_parser("init", help="Create an example run.yaml")

    list_parser = subparser.add_parser("list", aliases=["ls"], help="List Cloud Run services")

    describe_parser = subparser.add_parser("describe", aliases=["desc"],
                                           help="Describe Cloud Run service")
    describe_parser.add_argument("service", type=str, metavar="SERVICE",
                                 help="Name of the Cloud Run service")
    describe_parser.add_argument("--region", "-r", type=str, help="Region of the Cloud Run service",
                                 default="")

    add_verbose_quiet_flags([marathon_parser, init_parser, list_parser, describe_parser])

    return parser


def add_verbose_quiet_flags(parsers):
    for parser in parsers:
        parser.add_argument("--verbose", "-v", help="Set verbose mode (debug)",
                            action="store_true",
                            default=False)
        parser.add_argument("--quiet", "-q", help="Set quiet mode (only critical output)",
                            action="store_true",
                            default=False)
