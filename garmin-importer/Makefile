SHELL = /bin/bash -e
.RECIPEPREFIX := $(.RECIPEPREFIX)

test:
	sam validate --lint
	./scripts/run_tests.sh

fetch-latest:
	python ./scripts/fetch_latest_activity.py

build:
	 sam build GarminImporterFunction

deploy:
	sam deploy

local-invoke:
	sam local invoke GarminImporterFunction
