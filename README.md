# garmin-importer

This application takes activity data from Garmin Connect and saves it to private storage, so that it can be used by
applications like [dashed][dashed] to display custom summaries and statistics.

The importer runs as a single AWS Lambda that is responsible for regularly checking for new activities in Garmin Connect
, and when new activities are found, saving a cleaned up activity summary in DynamoDB, and the activity GPX and FIT
files on S3.


## Development

Use the facilities in the Makefile to test, build, local-invoke and deploy the function, from the repository root.

[dashed]: https://github.com/lancerinf/dashed
