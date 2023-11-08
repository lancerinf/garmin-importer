SHELL = /bin/bash -e
.RECIPEPREFIX := $(.RECIPEPREFIX)

test:
	./garmin-importer/scripts/run_tests.sh

fetch-latest:
	python ./garmin-importer/scripts/fetch_latest_activity.py

build:
	 sam build GarminImporterFunction --config-file samconfig.yaml --template garmin-importer/template.yaml --build-dir garmin-importer/.aws-sam/build --use-container

deploy:
	sam deploy --template garmin-importer/.aws-sam/build/template.yaml --config-file ../../samconfig.yaml

local-invoke:
	sam local invoke GarminImporterFunction --config-file ../../samconfig.yaml --template garmin-importer/.aws-sam/build/template.yaml
