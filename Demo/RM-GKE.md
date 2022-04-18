# Kubernetes Demo

## Setup
1. set environment variables in .env file
2. `cd Demo; ./install-dependencies.sh`

### GKE setup
To set up the GKE environment you can either follow the steps below or, to become more familiar with the GKE, follow the official tutorial [tutorial](https://cloud.google.com/kubernetes-engine/docs/tutorials/hello-app). After following the tutorial you will still want to walk through the steps below to ensure the `.env` file matches the GKE configuration. 

1. Create an [GKE account](https://cloud.google.com/kubernetes-engine)
2. create a project and add the Project ID (e.g. nomadic-line-311316) to the `.env` file as the `PROJECT_ID` variable. 
3. [Set up the SDK](https://cloud.google.com/sdk/docs/quickstart#linux)
4. Set up an Artifact Registry and ensure that `GCP_ARTIFACT_REPO` in the `.env` file matches the name. Do this by running: `make artifact-repo-gcr` then in the web console click `SETUP INSTRUCTIONS` and copy the command to get permission to push.

### Configure Influx

1. [Setup a cloud Influx account](https://docs.influxdata.com/influxdb/cloud/sign-up/ 
2. Create a bucket called `modicumdb`
3. Create a token
4. update `Demo/run/influx_cfg.py` with bucket, org(email used to register), the token, and the url (e.g. `https://us-central1-1.gcp.cloud2.influxdata.com/`)
6. [Set up influx cli](https://docs.influxdata.com/influxdb/cloud/tools/influx-cli/?t=Linux#set-up-the-influx-cli)

### Docker
1. add to .bashrc 
```
export DOCKER_BUILDKIT=1 
export COMPOSE_DOCKER_CLI_BUILD=1
```

## Start Compute clusters
### Pulsar Cluster

1. `make gke-cluster-up`
2. `make pulsar-gke-setup` 
3. `make pulsar-gke` Installs pulsar on cluster
4. `make pulsar-connect` configure kubectl to communicate with cluster
5. `make pulsar-services` get ip of pulsar-proxy and put in `run/cfg` file and set `standalone=False`
6. Check console, wait until pods are ready

### Create Market Cluster
Need to create a bigquery dataset `https://cloud.google.com/bigquery/docs/datasets`
1. In console click (`https://console.cloud.google.com/kubernetes`), `CREATE`->GKE Standard `CONFIGURE`
2. Cost-optimized cluster - use default values
3. Wait until cluster is created
4 `make gke-connect` connect to market cluster

## Start Framework
### Build and deploy framework
1. `make build-gcr`
2. `make push-gcr`
3. `make convert-gcr`
4. `make deploy-gcr`
5. takes about 2 minutes for container creation

## Stop Framework
1. `make delete`

# Cleaning up
When done with all experiments make sure to delete:
* https://console.cloud.google.com/compute/disks
* https://console.cloud.google.com/artifacts
* https://console.cloud.google.com/kubernetes

# Useful commands 

## Operations
1. `make check` Check status
2. `make scale` - Scale number of nodes. Modify Makefile as needed.
3. `docker system prune -a` - to delete all local images/containers.

## Debugging
* `kubectl get pods`
* Log into a pod
  * `make check` get pod name
  * `kubectl exec --stdin --tty <pod name> -- /bin/bash`


# Useful information
* https://console.cloud.google.com/iam-admin/quotas
* https://docs.influxdata.com/influxdb/cloud/api-guide/client-libraries/python/
* pip install 'influxdb-client[extra]'
* https://github.com/influxdata/influxdb-client-python
* https://docs.influxdata.com/influxdb/v2.0/query-data/get-started/query-influxdb/






