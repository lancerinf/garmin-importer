# garmin-importer

This application takes activity data from Garmin Connect and saves it to private storage, so that it can be used by other applications to display summaries, statistics.

It can be a collection of microservices with the following responsibility split:

* polling GarminConnect with some regularity. When new activities are found, the relevant data is taken and saved to private storage.
* raw data from private storage is processed, statictics are computed, results are stored.
* the latest available results are regularly loaded to a local-db that serves as datasource for the local grafana instance. On first startup when the local-db is empty, all results are loaded.
