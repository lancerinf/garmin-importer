SHELL = /bin/bash -e
.RECIPEPREFIX := $(.RECIPEPREFIX)

test:
	./garmin-importer/scripts/run_tests.sh

fetch-latest:
	python ./garmin-importer/scripts/fetch_latest_activity.py

build:
	sam build GarminImporterFunction --template garmin-importer/template.yaml --build-dir garmin-importer/.aws-sam/build --use-container

local-invoke:
	sam local invoke GarminImporterFunction --template garmin-importer/.aws-sam/build/template.yaml

deploy:
	sam deploy --guided --template-file garmin-importer/.aws-sam/build/template.yaml
