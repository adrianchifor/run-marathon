#!/usr/bin/env python3

import argparse

from marathon.version import description, version


def init_cli_parser():
    parser = argparse.ArgumentParser(prog="run", description=description)
    parser.add_argument("--version", action="version", version=version)
    subparser = parser.add_subparsers(help="commands")

    deploy_parser = subparser.add_parser("deploy", help="Deploy services to Cloud Run and setup IAM")
    deploy_parser.add_argument("service", type=str, metavar="SERVICE", nargs="?",
                              help="Service to deploy, default is all", default="all")

    build_parser = subparser.add_parser("build", help="Build containers using Cloud Build")
    build_parser.add_argument("service", type=str, metavar="SERVICE", nargs="?",
                              help="Service to build, default is all", default="all")

    init_parser = subparser.add_parser("init", help="Create an example run.yaml")

    check_parser = subparser.add_parser("check", help="Check that required gcloud services are enabled")

    list_parser = subparser.add_parser("list", aliases=["ls"], help="List Cloud Run services")

    describe_parser = subparser.add_parser("describe", aliases=["desc"],
                                           help="Describe Cloud Run service")
    describe_parser.add_argument("service", type=str, metavar="SERVICE", help="Service name")
    describe_parser.add_argument("--region", "-r", type=str, help="Service region", default="")

    invoke_parser = subparser.add_parser("invoke", help="Invoke Cloud Run service")
    invoke_parser.add_argument("service", type=str, metavar="SERVICE", help="Service name")
    invoke_parser.add_argument("--path", "-p", type=str, help="Request path, default is /", default="/")
    invoke_parser.add_argument("--request", "-X", type=str, help="Request method, default is GET", default="GET")
    invoke_parser.add_argument("--data", "-d", type=str, help="Request json data, default is \"\"", default="")
    invoke_parser.add_argument("--region", "-r", type=str, help="Service region", default="")

    add_verbose_quiet_flags([deploy_parser, build_parser, init_parser, check_parser, list_parser,
        describe_parser, invoke_parser])

    return parser


def add_verbose_quiet_flags(parsers):
    for parser in parsers:
        parser.add_argument("--verbose", "-v", help="Set verbose mode (debug)",
                            action="store_true",
                            default=False)
        parser.add_argument("--quiet", "-q", help="Set quiet mode (only critical output)",
                            action="store_true",
                            default=False)
