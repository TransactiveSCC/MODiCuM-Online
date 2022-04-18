include .env
export

gke-cluster-up:
	cd $(PULSAR_DEPEN)/charts; \
		PROJECT=$(PROJECT_ID) USE_LOCAL_SSD=true LOCAL_SSD_COUNT=4 scripts/pulsar/gke_bootstrap_script.sh up

pulsar-gke-setup:
	cd $(PULSAR_DEPEN)/pulsar-helm-chart; \
		./scripts/pulsar/prepare_helm_release.sh -n pulsar -k pulsar-modicum -c
	helm repo add apache https://pulsar.apache.org/charts
	helm repo update

pulsar-gke:
	helm upgrade --install pulsar apache/pulsar \
		--timeout 10m \
		--set initialize=true

pulsar-connect:
	gcloud container clusters get-credentials $(CLUSTER_NAME) --region $(REGION)-$(ZONE_EXTENSION)


pulsar-services:
	kubectl get service -n default


gke-connect:
	gcloud container clusters get-credentials $(MARKET_NAME) --region $(MARKET_REGION)-$(MARKET_ZONE_EXTENSION)

gke-update:
	gcloud container clusters update $(MARKET_NAME) --monitoring=SYSTEM

artifact-repo-gcr:
	gcloud artifacts repositories create $(GCP_ARTIFACT_REPO) --repository-format=docker --location=$(MARKET_REGION) --description="Docker repository"

build-gcr:
	cd $(MV2_Demo);\
		docker-compose -f docker-compose-gcr.yml build
	cd $(MV2_APP_SOURCE);\
		docker-compose -f docker-compose.yml build
	cd $(MV2_APP_SINK);\
		docker-compose -f docker-compose.yml build

push-gcr:
	cd $(MV2_Demo);\
		docker-compose -f docker-compose-gcr.yml push
	cd $(MV2_APP_SOURCE);\
		docker-compose -f docker-compose.yml push
	cd $(MV2_APP_SINK);\
		docker-compose -f docker-compose.yml push

convert-gcr:
	cd $(MV2_Demo);\
		kompose --file docker-compose-gcr.yml convert --replicas 1 --verbose -o deployments/ --volumes hostPath

deploy-gcr:
	cd $(MV2_Demo);\
		kubectl apply -f deployments

check:
	kubectl get pods

scale:
	kubectl scale --replicas=2 deployments/customer-service
	kubectl scale --replicas=2 deployments/supplier-service

delete:
	kubectl delete -f deployments


quota:
	kubectl get resourcequota gke-resource-quotas -o yaml

standalone-demo:
	cd service-examples/stress-ng && docker-compose build && docker-compose push
	influx delete --org "modicum" --bucket "modicumdb" --start 1970-01-01T00:00:00Z --stop 2022-01-01T00:00:00Z;
	docker-compose build;
	docker-compose up | tee run.txt