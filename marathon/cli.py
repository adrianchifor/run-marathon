#!/usr/bin/env python3

import os
import sys
import yaml
import logging

from threading import Thread

from marathon.cli_parser import init_cli_parser
from marathon.utils import get_marathon_config, init_marathon_config, interpolate_var
from marathon.utils import service_iter
from marathon import gcloud

log = logging.getLogger(__name__)


def main():
    parser = init_cli_parser()
    args = parser.parse_args()

    try:
        cmd = sys.argv[1]
    except IndexError:
        parser.print_help()
        sys.exit(1)

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG,
                            format="%(asctime)s %(levelname)s -- %(message)s")
    elif args.quiet:
        logging.basicConfig(level=logging.CRITICAL, format="%(message)s")
    else:
        logging.basicConfig(level=logging.INFO, format="%(message)s")

    handle_command(cmd, args)


def handle_command(command, args):
    if command == "marathon":
        run_marathon(args)

    elif command == "init":
        run_init()

    elif command == "list" or command == "ls":
        gcloud.list()

    elif command == "describe" or command == "desc":
        gcloud.describe(args.service, args.region)


def run_marathon(args):
    try:
        conf = get_marathon_config()
        if args.build:
            build_threads = []
            for service in service_iter():
                try:
                    dir = interpolate_var(conf[service]["dir"])
                    image = interpolate_var(conf[service]["image"])
                    t = Thread(target=gcloud.build, args=(service, dir, image))
                    build_threads.append(t)
                    log.info(f"Building {service}")
                except KeyError:
                    log.error(f"Failed to build {service}: 'dir' and 'image' are required in run.yaml")

            for t in build_threads:
                t.start()

            log.info(("Build logs available at: https://console.cloud.google.com/cloud-build/"
                f"builds?project={conf['project']}"))
            log.info("Waiting for builds to finish...")

            for t in build_threads:
                t.join()

        # TODO: deploy

    except Exception as e:
        log.error(e)
        log.info("You can create an example run.yaml with 'run init'")
        sys.exit(1)


def run_init():
    if os.path.exists("run.yaml"):
        log.info("run.yaml already exists, skipping init")
        return

    log.info("An example run.yaml will be created in the current directory.")
    log.info("Please enter a project and default region where you want to deploy the Cloud Run services.\n")
    try:
        project = input("Google Cloud project: ")
        region = input("Google Cloud default region: ")
    except KeyboardInterrupt:
        log.info("\nStopping init ...")
        sys.exit(1)

    run_yaml = init_marathon_config()
    if project:
        run_yaml["project"] = project
    if region:
        run_yaml["region"] = region

    with open("run.yaml", "w") as f:
        yaml.dump(run_yaml, stream=f)
        log.info("Created example run.yaml")
