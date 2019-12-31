#!/usr/bin/env python3

import os
import sys
import yaml
import logging

from threading import Thread
from toposort import toposort_flatten, CircularDependencyError

from marathon.cli_parser import init_cli_parser
from marathon.utils import get_marathon_config, init_marathon_config, interpolate_var
from marathon.utils import service_iter, service_dependencies
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
    if command == "deploy":
        run_deploy(args)

    elif command == "build":
        run_build(args)

    elif command == "init":
        run_init()

    elif command == "check":
        gcloud.check()

    elif command == "list" or command == "ls":
        gcloud.list()

    elif command == "describe" or command == "desc":
        gcloud.describe(args.service, args.region)

    elif command == "invoke":
        gcloud.invoke(args)


def run_deploy(args):
    try:
        conf = get_marathon_config()
        project = conf["project"]
    except Exception as e:
        log.error(e)
        log.info("You can create an example run.yaml with 'run init'")
        sys.exit(1)

    log.info(f"Deployment status: https://console.cloud.google.com/run?project={project}")

    if args.service != "all":
        log.info(f"Deploying {args.service} ...")
        gcloud.deploy(args.service)
    else:
        services_deps_order, services_nodeps = service_dependencies()
        try:
            services_deps_order = toposort_flatten(services_deps_order)
        except CircularDependencyError as e:
            log.error(e)
            log.error("Deployment failed: Double check the service links in run.yaml")
            sys.exit(1)

        services_deploy_parallel = list(set(services_nodeps) - set(services_deps_order))
        deploy_threads = []
        for service in services_deploy_parallel:
            t = Thread(target=gcloud.deploy, args=(service,))
            deploy_threads.append(t)
            log.info(f"Deploying {service} ...")

        for t in deploy_threads:
            t.start()

        for service in services_deps_order:
            log.info(f"Deploying {service} ...")
            success = gcloud.deploy(service)
            if not success:
                log.error(f"{service} has dependants, canceling after other deployments finish ...")
                try:
                    for t in deploy_threads:
                        t.join()
                except KeyboardInterrupt:
                    pass
                log.error("\nDeployments cancelled\n")
                sys.exit(1)

        log.info("Waiting for deployments to finish ...")

        try:
            for t in deploy_threads:
                t.join()
        except KeyboardInterrupt:
            log.error("\nDeployments cancelled\n")
            sys.exit(1)

    log.info("\nDeployments finished\n")


def run_build(args):
    try:
        conf = get_marathon_config()
        project = conf["project"]
    except Exception as e:
        log.error(e)
        log.info("You can create an example run.yaml with 'run init'")
        sys.exit(1)

    log.info(("Build logs: https://console.cloud.google.com/cloud-build/"
        f"builds?project={project}"))

    if args.service != "all":
        log.info(f"Building {args.service} ...")
        gcloud.build(args.service)
    else:
        images_built = []
        build_threads = []
        for service in service_iter():
            if "dir" not in conf[service]:
                log.info(f"Skipping {service}: No 'dir' specified in run.yaml")
                continue
            if "image" not in conf[service]:
                log.error(f"Failed to build {service}: 'image' is required in run.yaml")
                continue

            image = interpolate_var(conf[service]["image"])
            if image in images_built:
                log.info(f"Skipping {service}: Image already built in another service")
                continue
            images_built.append(image)

            t = Thread(target=gcloud.build, args=(service,))
            build_threads.append(t)
            log.info(f"Building {service} ...")

        for t in build_threads:
            t.start()

        log.info("Waiting for builds to finish ...")

        try:
            for t in build_threads:
                t.join()
        except KeyboardInterrupt:
            log.error("\nBuilds cancelled\n")
            sys.exit(1)

    log.info("\nBuilds finished\n")


def run_init():
    if os.path.exists("run.yaml"):
        log.info("run.yaml already exists, skipping init")
        return

    log.info("An example run.yaml will be created in the current directory.")
    log.info("Enter a project and default region where you want to deploy the Cloud Run services.\n")
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

    user = gcloud.get_user_email()
    if user:
        run_yaml["allow-invoke"][0] = f"user:{user.strip()}"

    with open("run.yaml", "w") as f:
        yaml.dump(run_yaml, stream=f)
        log.info("Created example run.yaml")
