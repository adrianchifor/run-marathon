# run-marathon
Manage and simplify your Cloud Run deployments.

Work in progress.

Not affiliated with https://mesosphere.github.io/marathon/.

Test:
```
cd example
# Build and deploy
run deploy --build  # TODO: implement deploy
# Check running containers
run ls
```

run.yaml config:
```
project: Google Cloud project           # required
region: default region where we deploy  # required
allow_invoke:                           # optional, users allowed to `run invoke <service>`
  - user:your_user@domain.com
  - group:your_group@domain.com

service1:
  image: gcr.io/${project}/service1:latest  # required, yes you can interpolate first-level variables :)
  dir: apps/service1   # only needed when using --build in 'run deploy'
  authenticated: true  # optional, default true, set to false to make the service public
  region: your_region  # optional, defaults to the region specified at first-level
  concurrency: 30      # optional, default 80
  max-instances: 1000  # optional, default quota is 1000
  memory: 512Mi        # optional, default 256Mi max 2Gi
  timeout: 30          # optional, default 300 (5min)
  env:
    KEY: VALUE
  labels:
    KEY: VALUE
  cloudsql-instances:
    - your_cloudsql_instance
  iam_roles:
    - roles/compute.viewer  # these get attached to the service account of the service
  links:
    - service2              # allowed to invoke service2 through IAM, also injects SERVICE2_URL env into the container
```

TODO:
- Invoke function
- Only deploy if container image or config changes (persist + check combo hash)
- Support domain mappings
- Cleanup unused IAM service accounts and bindings
- Support pubsub
- Support cron
