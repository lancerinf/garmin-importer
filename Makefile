.RECIPEPREFIX := $(.RECIPEPREFIX)

build:
	sam build GarminImporterFunction --template garmin-importer/template.yaml --build-dir garmin-importer/.aws-sam/build --use-container

local-invoke:
	sam local invoke GarminImporterFunction --template garmin-importer/.aws-sam/build/template.yaml
