# Cloud Run Marathon

Simplify and manage your serverless container deployments. Like docker-compose but for [Cloud Run](https://cloud.google.com/run/).

Not affiliated with https://mesosphere.github.io/marathon/.

<img src="./cloud-run.jpg" width="329">

## Quickstart

### Install (python 3.6+):
```
pip3 install --user run-marathon
```

Also [install gcloud SDK](https://cloud.google.com/sdk/install) and [initialize it](https://cloud.google.com/sdk/docs/authorizing).

### Example:
```
cd example/

# Initialize config file
rm run.yaml && run init

# Check that required gcloud services are enabled
run check

# Build containers with Cloud Build
run build

# Deploy to Cloud Run
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

allow_invoke:                            # optional, users allowed to `run invoke <service>`
  - user:your_user@domain.com
  - group:your_group@domain.com

service1:
  image: gcr.io/${project}/service1:latest   # required, yes you can interpolate first-level variables :)
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
  cloudsql-instances:
    - your_cloudsql_instance
  iam_roles:                  
    - roles/compute.viewer   # these get attached to the service account of the service
  links:                      
    - service2               # allow invocation through IAM, also injects SERVICE2_URL into env

service2:
  dir: apps/service2
  image: gcr.io/${project}/service2:latest
```

## TODO
- Only deploy if container image or config changes (persist + check combo hash)
- Support domain mappings
- Cleanup unused IAM service accounts and bindings
- Support pubsub
- Support cron
