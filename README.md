# run-marathon
Manage and simplify your Cloud Run deployments.

Work in progress.

Not affiliated with https://mesosphere.github.io/marathon/.

Install (py 3.6+):
```
pip3 install --user run-marathon
```

Test:
```
cd example
rm run.yaml && run init
run build
run deploy
run ls
run describe service1
run invoke service1
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
  dir: apps/service1          # only needed when using --build in 'run deploy'
  authenticated: true         # optional, default true, set to false to make the service public
  region: your_region         # optional, defaults to the region specified at first-level
  concurrency: 30             # optional, default 80
  max-instances: 1000         # optional, default quota is 1000
  memory: 512Mi               # optional, default 256Mi max 2Gi
  timeout: 30                 # optional, default 300 (5min)
  env:                        # optional
    KEY: VALUE
  labels:                     # optional
    KEY: VALUE
  cloudsql-instances:         # optional
    - your_cloudsql_instance
  iam_roles:                  # optional, these get attached to the service account of the service
    - roles/compute.viewer
  links:                      # optional, e.g. allow service1 -> service2 through IAM, also injects SERVICE2_URL into env
    - service2
```

TODO:
- Only deploy if container image or config changes (persist + check combo hash)
- Support domain mappings
- Cleanup unused IAM service accounts and bindings
- Support pubsub
- Support cron
