# Cloud Run Marathon

Simplify and manage your serverless container deployments. Like docker-compose but for [Cloud Run](https://cloud.google.com/run/).

_Note: This is currently in alpha and under heavy development and iteration. If you have ideas or feedback, please open an issue and we can discuss._

#### What's Cloud Run?
Cloud Run [is now GA](https://cloud.google.com/blog/products/serverless/knative-based-cloud-run-services-are-ga) and it allows you to run your containers in a fully managed, production-ready environment leveraging features like autoscaling (including scaling to 0), regional redundancy, integrated monitoring and logging, easy integration with CloudSQL/PubSub/Tasks/Scheduler, automatic TLS endpoints, authentication, IAM policies, and isolation based on [gvisor](https://gvisor.dev/). All of this with a very generous free tier (2mil req/month) and [pay-per-use pricing](https://cloud.google.com/run/#pricing). Sounds like a pretty sweet deal!

#### Ok.. then what's Cloud Run Marathon?
**Cloud Run Marathon is to Cloud Run what docker-compose is to Docker, essentially a nice wrapper to simplify, manage and automate.**

If you have just one container `docker run ..` or `gcloud run deploy ..` will do the trick, but when you have more containers with configs, policies, interactions, dependencies and so on, it gets a bit more complex.

#### Options and reducing friction
The process of getting code and containers into production is still quite slow and cumbersome with a lot of friction. Sure you can just spin up a managed Kubernetes cluster and start deploying but the time/resource cost, barrier to entry and ops overhead is massive for most engineers and companies.

The whole point of this tool is to reduce friction. Before this, I managed my Cloud Run deployments with gcloud CLI and Terraform, which were the only two reasonable options, but still, Terraform requires a big time investment to get right and plain gcloud CLI is a hassle to write and maintain so these are not feasible solutions for reducing friction.

I have fond memories of docker-compose and it was maybe the most convenient way to manage complex container deployments before the orchestration wars began. So I thought I'd base the design of this tool on that, with some cloud native sprinkled on top.

Let's `run` and get to the finish line sooner, and only then the real journey begins.

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
run build

# Deploy to Cloud Run and setup IAM
run deploy

run ls
run describe service1
run invoke service1 # or visit URL

# Request flow:
#
# user -----> service1 -----> service2 -----> service3
#      public          private         private   |
#                                                |
# "Hello from service3" <-------------------------
```

## Configuration (run.yaml)
```
project: Google Cloud project            # required
region: default region where we deploy   # required

# optional, users allowed to `run invoke <service>`
allow_invoke:                            
  - user:your_user@domain.com
  - group:your_group@domain.com

service1:
  # required, yes you can interpolate first-level variables :)
  image: gcr.io/${project}/service1:latest   
  dir: apps/service1     # only needed in 'run build'
  authenticated: false   # default true, set to false to make the service public
  region: your_region    # defaults to the region specified at first-level
  concurrency: 30        # default 80
  max-instances: 1000    # default quota is 1000
  memory: 512Mi          # default 256Mi max 2Gi
  timeout: 30            # default 300 (5min)
  env:              
    KEY: VALUE
  labels:
    KEY: VALUE

  # roles/cloudsql.client will be automatically added to the service account on deployment
  cloudsql-instances:        
    - instance_name

  # these roles will be automatically added to the service account on deployment
  iam_roles:                  
    - roles/compute.viewer

  # allows invocation through IAM + injects SERVICE2_URL into env
  links:                      
    - service2               

  # invokes your service on a schedule using a Cloud Scheduler job
  cron:                      
    schedule: "0 * * * *"      
    path: /                  # default /
    http-method: post        # default post

service2:
  dir: apps/service2
  image: gcr.io/${project}/service2:latest
```

## TODO
- Only deploy if container image or config changes (persist + check combo hash)
- Support domain mappings
- Cleanup unused IAM service accounts and bindings
- Support pubsub

This project is not affiliated with https://mesosphere.github.io/marathon/.
