# Cloud Run Marathon

Simplify and manage your serverless container deployments. Like docker-compose but for [Cloud Run](https://cloud.google.com/run/).

#### What's Cloud Run?
Cloud Run [is now GA](https://cloud.google.com/blog/products/serverless/knative-based-cloud-run-services-are-ga) and it allows you to run your containers in a fully managed, production-ready environment leveraging features like:
- Autoscaling (including scaling to 0)
- Regional redundancy
- Integrated monitoring and logging
- Easy integration with CloudSQL/PubSub/Tasks/Scheduler
- Automatic TLS endpoints
- Authentication and IAM policies
- Isolation based on [gvisor](https://gvisor.dev/)

All of this with a very generous free tier (2mil req/month) and [pay-per-use pricing](https://cloud.google.com/run/#pricing). Sounds like a pretty sweet deal!

#### Ok.. then what's Cloud Run Marathon?
**Cloud Run Marathon is to Cloud Run what docker-compose is to Docker, essentially a nice wrapper to simplify, manage and automate.**

If you have just one container `docker run ..` or `gcloud run deploy ..` will do the trick, but when you have multiple containers with configs, policies, interactions, dependencies and so on, it gets a bit more complex.

This tool is designed to reduce the friction and cost (mainly time) of getting more complex containers/microservices into production, compared to alternatives like Kubernetes, Terraform or just plain gcloud CLI.

<img src="./cloud-run.jpg" width="329">

## Quickstart

### Install (python 3.6+)
```
$ pip3 install --user run-marathon

$ run --help
usage: run [-h] [--version]
           {deploy,build,init,check,list,ls,describe,desc,invoke} ...

Simplify and manage your serverless container deployments. Like docker-compose
but for Cloud Run.

positional arguments:
  {deploy,build,init,check,list,ls,describe,desc,invoke}
                        commands
    deploy              Deploy services to Cloud Run and setup IAM
    build               Build containers using Cloud Build
    init                Create an example run.yaml
    check               Check that required gcloud services are enabled
    list (ls)           List Cloud Run services
    describe (desc)     Describe Cloud Run service
    invoke              Invoke Cloud Run service

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
```

Also [install gcloud SDK](https://cloud.google.com/sdk/install) and [initialize it](https://cloud.google.com/sdk/docs/authorizing).

### Simple example
```
cd example/

# Initialize config file
rm run.yaml && run init

# Check that required gcloud services are enabled
run check

# Build containers with Cloud Build
# Running "gcloud config set builds/use_kaniko True" will enable Kaniko builds and layer caching
run build

# Deploy to Cloud Run and setup IAM
run deploy

run ls
run describe service1
run invoke service1 # or visit URL

# Request flow:
#
# user -----> service1 -----> service2 -----> service3 (also has hourly cron)
#      public          private         private   |
#                                                |
# "Hello from service3" <-------------------------
```

## Configuration (run.yaml)

The configuration structure and options of the `run.yaml` file. Items not market with 'required' are optional or have a default. You can interpolate first-level variables, like the project or region, with the following notation: `${<variable name>}`, e.g. `image: gcr.io/${project}/service1:latest`.

See [example/run.yaml](https://github.com/adrianchifor/run-marathon/blob/master/example/run.yaml) for a simple configuration example.

#### project (required)
Google Cloud Project

#### region (required)
Default region where you want to deploy, e.g. `europe-west1`

#### allow-invoke
The users or groups allowed to `run invoke <service>`, example:
```
allow-invoke:              
  - user:a_user@domain.com
  - group:a_group@domain.com
```

#### [service]
A service definition and its configuration

* **image** (required)
<br>Container image to deploy and/or build, e.g. `gcr.io/${project}/service1:latest`

* **dir** (required only for `run build`)
<br>The directory of the service and Dockerfile to use for building the container, e.g. `apps/service1`

* **authenticated**
<br>Default `true`, set to `false` to make the service public

* **region**
<br>Defaults to the region specified at first-level

* **concurrency**
<br>Number of concurrent requests one container can receive, default `80`

* **max-instances**
<br>Maximum number of containers, default quota is `1000` (can be raised)

* **cpu**
<br>CPUs to allocate to each container, default `1`, can also be `2`

* **memory**
<br>Memory to allocate to each container, default `256Mi`, max `2Gi`

* **timeout**
<br>Number of seconds until a request to a container times out, default `300`

* **port**
<br>Container port, also overrides the PORT env var, default `8080`

* **command**
<br>Overrides the entrypoint of the container

* **args**
<br>Arguments to pass to the container command
  ```
  args:
    - --flag1
    - --flag2
  ```

* **env**
<br>Environment variables to add to containers
  ```
  env:
    KEY: VALUE
  ```

* **vpc-connector**
<br>VPC Connector for the Cloud Run service

* **labels**
<br>GCP labels to add to the Cloud Run service
  ```
  labels:
    KEY: VALUE
  ```

* **cloudsql-instances**
<br>List of CloudSQL instances to attach to the containers. A unix domain socket will be created per CloudSQL instance in each container at `/cloudsql/<instance_name>` for MySQL and `/cloudsql/<instance_name>/.s.PGSQL.5432` for PostgreSQL. `roles/cloudsql.client` will be automatically added to the IAM service account of the service on deployment
  ```
  cloudsql-instances:
    - instance_name
  ```

* **iam-roles**
<br>IAM roles to attach to the service account of the service
  ```
  iam-roles:
    - roles/compute.viewer
  ```

* **links**
<br>Creates links to other services by allowing invocation through IAM and by injecting the service URLs into the environment variables on deployment. For the example below, `SERVICE2_URL` will be injected into `service1` env
  ```
  service1:
    links:
      - service2
  ```

* **cron**
<br>Creates a Cloud Scheduler job and invokes the service on the specified schedule
  * **schedule** (required)
  <br>Cron expression, e.g. `"0 * * * *"`
  * **path**
  <br>URL path for the invocation request, defaults to `/`
  * **http-method**
  <br>HTTP method used for the invocation request, defaults to `post`


## TODO
- Support PubSub
- Only deploy if container image or config changes (persist + check combo hash)
- Support domain mappings
- Cleanup unused IAM service accounts and bindings
- Document the commands in more depth
- A more complex example
- Allow custom variables on first-level in run.yaml

## License

Copyright © 2020 Adrian Chifor

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

This project is not affiliated with https://mesosphere.github.io/marathon/.
