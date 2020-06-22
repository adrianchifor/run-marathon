#!/usr/bin/env python3

import sys
import logging
import subprocess
import json
import re
import http.client as http

from marathon.utils import get_marathon_config, interpolate_var, sanitize_service_name

log = logging.getLogger(__name__)


def get_user_email():
    user = None
    try:
        user, _ = eval_noout("gcloud config get-value account")
    except Exception:
        pass
    return user


def build(service):
    conf = get_marathon_config()
    if "project" not in conf or "dir" not in conf[service] or "image" not in conf[service]:
        log.error((f"Failed to build {service}: 'project', '{service}.dir' and '{service}.image'"
                   " are required in run.yaml"))
        return

    dir = interpolate_var(conf[service]["dir"])
    image = interpolate_var(conf[service]["image"])
    eval_noout(f"gcloud builds submit --tag={image} {dir} --project={conf['project']}")


def deploy(service):
    conf = get_marathon_config()
    if "project" not in conf or "region" not in conf or "image" not in conf[service]:
        log.error(
            f"Failed to deploy {service}: 'project', 'region' and '{service}.image' are required in run.yaml")
        return False

    project = conf["project"]
    region = interpolate_var(conf.get("region", conf["region"]))
    image = interpolate_var(conf[service]["image"])

    service_account = setup_service_iam(service, project, region)

    log.debug(f"Deploying {service} with configuration: {conf[service]}")

    sanitized_service = sanitize_service_name(service)

    deploy_cmd = (f"gcloud beta run deploy {sanitized_service} --image={image} --platform=managed"
                  f" --region={region} --project={project} --service-account={service_account}")
    deploy_cmd += complete_deploy_cmd(service, project, region)

    log.debug(deploy_cmd)
    eval_noout(deploy_cmd)

    if "cron" in conf[service]:
        setup_cron(service, project, region)

    allow_invoke(service, project, region)

    deployed_url = get_service_endpoint(sanitized_service, project, region)
    if deployed_url:
        log.info(f"[{service}]: {deployed_url}")

    return True


def setup_service_iam(service, project, region):
    conf = get_marathon_config()
    sanitized_service = sanitize_service_name(service)
    service_account_name = f"{sanitized_service}-sa"
    service_account_email = f"{service_account_name}@{project}.iam.gserviceaccount.com"

    if not service_account_exists(service_account_email, project):
        log.debug(f"Creating service account for {service} ...")
        eval_stdout(
            f"gcloud iam service-accounts create {service_account_name} --project={project}")

    if "iam-roles" in conf[service]:
        for role in conf[service]["iam-roles"]:
            log.debug(f"Adding {role} to {service} service account ...")
            eval_noout((f"gcloud projects add-iam-policy-binding {project}"
                        f" --member=serviceAccount:{service_account_email} --role={role}"
                        f" --project={project}"))

    if "cloudsql-instances" in conf[service] and len(conf[service]["cloudsql-instances"]) > 0:
        log.debug(f"Adding CloudSQL Client permission to {service} service account ...")
        eval_noout((f"gcloud projects add-iam-policy-binding {project}"
                    f" --member=serviceAccount:{service_account_email} --role=roles/cloudsql.client"
                    f" --project={project}"))

    if "links" in conf[service]:
        for linked_service in conf[service]["links"]:
            log.debug(f"Allowing {service} -> {linked_service} invocation ...")
            linked_service_sanitized = sanitize_service_name(linked_service)
            eval_noout((f"gcloud run services add-iam-policy-binding {linked_service_sanitized}"
                        f" --member=serviceAccount:{service_account_email} --role=roles/run.invoker"
                        f" --platform=managed --project={project} --region={region}"))

    return service_account_email


def complete_deploy_cmd(service, project, region):
    conf = get_marathon_config()
    deploy_cmd = ""

    authenticated = True
    if "authenticated" in conf[service]:
        authenticated = (interpolate_var(conf[service]["authenticated"]).lower() == 'true')
    if authenticated:
        deploy_cmd += " --no-allow-unauthenticated"
    else:
        deploy_cmd += " --allow-unauthenticated"

    if "concurrency" in conf[service]:
        deploy_cmd += f" --concurrency={interpolate_var(conf[service]['concurrency'])}"

    if "max-instances" in conf[service]:
        deploy_cmd += f" --max-instances={interpolate_var(conf[service]['max-instances'])}"

    if "cpu" in conf[service]:
        deploy_cmd += f" --cpu={interpolate_var(conf[service]['cpu'])}"

    if "memory" in conf[service]:
        deploy_cmd += f" --memory={interpolate_var(conf[service]['memory'])}"

    if "timeout" in conf[service]:
        deploy_cmd += f" --timeout={interpolate_var(conf[service]['timeout'])}"

    if "port" in conf[service]:
        deploy_cmd += f" --port={interpolate_var(conf[service]['port'])}"

    if "command" in conf[service]:
        deploy_cmd += f" --command={interpolate_var(conf[service]['command'])}"

    if "args" in conf[service] and len(conf[service]["args"]) > 0:
        args = ""
        for arg in conf[service]["args"]:
            args += f"{interpolate_var(arg)},"
        # Remove trailing comma
        if args.endswith(","):
            args = args[:-1]
        if len(args) > 0:
            deploy_cmd += f" --args={args}"

    if "vpc-connector" in conf[service]:
        deploy_cmd += f" --vpc-connector={interpolate_var(conf[service]['vpc-connector'])}"

    envs = ""
    if "env" in conf[service] and len(conf[service]["env"]) > 0:
        for key, value in conf[service]["env"].items():
            envs += f"{interpolate_var(key)}={interpolate_var(value)},"
        # Remove trailing comma
        if envs.endswith(","):
            envs = envs[:-1]

    if "links" in conf[service] and len(conf[service]["links"]) > 0:
        for link in conf[service]["links"]:
            interpolated_link = interpolate_var(link)
            url = get_service_endpoint(sanitize_service_name(interpolated_link), project, region)
            if url:
                env_link_key = interpolated_link.upper().replace("-", "_") + "_URL"
                envs += f",{env_link_key}={url}"
        # Remove starting comma if no previous envs exist
        if envs.startswith(","):
            envs = envs[1:]

    if len(envs) > 0:
        deploy_cmd += f" --set-env-vars={envs}"

    if "labels" in conf[service] and len(conf[service]["labels"]) > 0:
        labels = ""
        for key, value in conf[service]["labels"].items():
            labels += f"{interpolate_var(key)}={interpolate_var(value)},"
        # Remove trailing comma
        if labels.endswith(","):
            labels = labels[:-1]
        if len(labels) > 0:
            deploy_cmd += f" --clear-labels --labels={labels}"

    if "cloudsql-instances" in conf[service] and len(conf[service]["cloudsql-instances"]) > 0:
        cloudsql_instances = ""
        for instance in conf[service]["cloudsql-instances"]:
            cloudsql_instances += f"{interpolate_var(instance)},"
        # Remove trailing comma
        if cloudsql_instances.endswith(","):
            cloudsql_instances = cloudsql_instances[:-1]
        if len(cloudsql_instances) > 0:
            deploy_cmd += f" --set-cloudsql-instances={cloudsql_instances}"

    return deploy_cmd


def setup_cron(service, project, region):
    conf = get_marathon_config()
    sanitized_service = sanitize_service_name(service)
    cron_sa_name = f"run-scheduler-invoker-sa"
    cron_sa_email = f"{cron_sa_name}@{project}.iam.gserviceaccount.com"

    cron_config = conf[service]["cron"]
    if "schedule" not in cron_config:
        log.error(f"No 'schedule' specified in cron config for {service} in run.yaml")
        return

    if not service_account_exists(cron_sa_email, project):
        log.debug(f"Creating Cloud Scheduler service account ...")
        eval_stdout(f"gcloud iam service-accounts create {cron_sa_name} --project={project}")

    log.debug(f"Allowing Cloud Scheduler -> {service} invocation ...")
    eval_noout((f"gcloud run services add-iam-policy-binding {sanitized_service}"
                f" --member=serviceAccount:{cron_sa_email} --role=roles/run.invoker"
                f" --platform=managed --project={project} --region={region}"))

    scheduler_cmd_type = "update"
    scheduler_list_json, _ = eval_noout(("gcloud scheduler jobs list --format=json"
                                         f" --project={project} --filter=name:/jobs/{sanitized_service}-job"))
    scheduler_list = json.loads(scheduler_list_json)
    if len(scheduler_list) == 0:
        scheduler_cmd_type = "create"

    service_endpoint = get_service_endpoint(sanitized_service, project, region)
    if service_endpoint:
        if scheduler_cmd_type == "create":
            log.info(f"Creating Cloud Scheduler job for {service} ...")
        cron_cmd = (f"gcloud scheduler jobs {scheduler_cmd_type} http {sanitized_service}-job"
                    f" --http-method={cron_config.get('http-method', 'post').lower()}"
                    f" --uri={service_endpoint}{cron_config.get('path', '/')}"
                    f" --oidc-service-account-email={cron_sa_email}"
                    f" --oidc-token-audience={service_endpoint}"
                    f" --project={project}").split(" ")
        cron_cmd.append(f"--schedule={cron_config['schedule']}")
        eval_stdout(cron_cmd, split=False)
    else:
        log.error(f"Failed to create/update Cloud Scheduler job for {service}, no service endpoint")


def service_account_exists(service_account_email, project):
    sa_list_json, _ = eval_noout(("gcloud iam service-accounts list --format=json"
                                  f" --project={project} --filter=email:{service_account_email}"))
    sa_list = json.loads(sa_list_json)
    if len(sa_list) == 0:
        return False
    return True


def allow_invoke(service, project, region):
    conf = get_marathon_config()
    sanitized_service = sanitize_service_name(service)

    if "allow-invoke" in conf:
        for member in conf["allow-invoke"]:
            if isinstance(member, dict):
                member = json.dumps(member)
            # Remove {, }, ", ' and all whitespace characters
            sanitized_member = re.sub("[{}\"\'\s]", "", member)
            log.debug(f"Allowing {sanitized_member} -> {service} invocation ...")
            eval_noout((f"gcloud run services add-iam-policy-binding {sanitized_service}"
                        f" --member={sanitized_member} --role=roles/run.invoker"
                        f" --platform=managed --project={project} --region={region}"))


def check():
    cmd = "gcloud services list --format=json"
    project = ""
    try:
        project = get_marathon_config()["project"]
        cmd += f" --project={project}"
    except Exception:
        log.debug("Could not get project from run.yaml, using gcloud default")

    result_json, _ = eval_noout(cmd)
    enabled_svc = [svc["config"]["name"] for svc in json.loads(result_json)]

    all_enabled = True
    if "run.googleapis.com" not in enabled_svc:
        all_enabled = False
        log.info(("Cloud Run API is not enabled. Enable it"
                  f" at: https://console.cloud.google.com/apis/library/run.googleapis.com?project={project}"))
    if "cloudbuild.googleapis.com" not in enabled_svc:
        all_enabled = False
        log.info(("Cloud Build API is not enabled. If you want to use 'run build' enable it"
                  f" at: https://console.cloud.google.com/apis/library/cloudbuild.googleapis.com?project={project}"))
    if "containerregistry.googleapis.com" not in enabled_svc:
        all_enabled = False
        log.info(("Cloud Container Registry API is not enabled. If you want to use 'run build' enable it"
                  f" at: https://console.cloud.google.com/apis/library/containerregistry.googleapis.com?project={project}"))
    if "pubsub.googleapis.com" not in enabled_svc:
        all_enabled = False
        log.info(("Cloud PubSub API is not enabled. If you use PubSub in your services enable it"
                  f" at: https://console.cloud.google.com/apis/library/pubsub.googleapis.com?project={project}"))
    if "cloudscheduler.googleapis.com" not in enabled_svc:
        all_enabled = False
        log.info(("Cloud Scheduler API is not enabled. If you trigger services on a cron schedule enable it"
                  f" at: https://console.cloud.google.com/apis/library/cloudscheduler.googleapis.com?project={project}"))

    if all_enabled:
        log.info("Cloud Run, Build, Container Registry, PubSub and Scheduler APIs are enabled. All good!")


def list():
    try:
        project = get_marathon_config()["project"]
        eval_stdout(f"gcloud run services list --platform=managed --project={project}")
    except Exception:
        log.debug("Could not get project from run.yaml, using gcloud default")
        eval_stdout("gcloud run services list --platform=managed")


def describe(service, region):
    if not region:
        try:
            region = get_marathon_config()["region"]
        except Exception:
            log.error(("Specify a region, either in run.yaml or in "
                       "'run describe <service> --region=<region>'"))
            sys.exit(1)

    sanitized_service = sanitize_service_name(service)
    try:
        project = get_marathon_config()["project"]
        eval_stdout((f"gcloud run services describe {sanitized_service}"
                     f" --platform=managed --region={region} --project={project}"))
    except Exception:
        log.debug("Could not get project from run.yaml, using gcloud default")
        eval_stdout(f"gcloud run services describe {sanitized_service}"
                    f" --platform=managed --region={region}")


def invoke(args):
    region = args.region
    if not region:
        try:
            region = get_marathon_config()["region"]
        except Exception:
            log.error(("Specify a region, either in run.yaml or in "
                       "'run invoke <service> --region=<region>'"))
            sys.exit(1)

    sanitized_service = sanitize_service_name(args.service)
    project = None
    try:
        project = get_marathon_config()["project"]
    except Exception:
        pass

    token = get_auth_token()
    if not token:
        log.error(("Could not get gcloud identity token. Make sure gcloud is correctly"
                   " setup and authorized (https://cloud.google.com/sdk/docs/authorizing)"))
        sys.exit(1)

    service_url = get_service_endpoint(sanitized_service, project, region)
    if service_url:
        auth_header = {"Authorization": f"Bearer {token.strip()}"}

        try:
            conn = http.HTTPSConnection(service_url.replace("https://", ""), 443)
            conn.request(args.request.upper(), args.path, args.data, auth_header)
            log.info(conn.getresponse().read().decode())
            conn.close()
        except Exception as e:
            log.error(e)
            sys.exit(1)


def get_auth_token():
    token = None
    try:
        token, _ = eval_noout("gcloud auth print-identity-token")
    except Exception:
        pass
    return token


def get_service_endpoint(service, project, region):
    url = None
    if project:
        service_json, _ = eval_noout((f"gcloud run services describe {service} --platform=managed"
                                      f" --format=json --region={region} --project={project}"))
    else:
        log.debug("get_service_endpoint: No project provided, using gcloud default")
        service_json, _ = eval_noout((f"gcloud run services describe {service} --platform=managed"
                                      f" --format=json --region={region}"))
    try:
        url = json.loads(service_json)["status"]["address"]["url"]
    except Exception as e:
        log.debug(e)
        log.info(f"Failed to get service endpoint for {service}. Use --verbose for more info")

    return url


def eval_stdout(command, split=True):
    if split:
        command = command.split(" ")
    try:
        proc = subprocess.Popen(command)
        proc.communicate()
    except FileNotFoundError:
        gcloud_not_installed()


def eval_noout(command, split=True):
    if split:
        command = command.split(" ")
    try:
        pipe = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = pipe.communicate()
        return (out.decode(), err.decode())
    except FileNotFoundError:
        gcloud_not_installed()


def gcloud_not_installed():
    log.error("gcloud not installed, check https://cloud.google.com/sdk/install")
    sys.exit(1)
