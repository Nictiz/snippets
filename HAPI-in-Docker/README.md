# HAPI in Docker

Docker config for quickly (and dirtily) running a local HAPI FHIR server for testing and debugging. It is modified from the official documentation at https://hub.docker.com/r/hapiproject/hapi.

## Using

To run, it should be enough to have Docker/Podman running and to type:

> docker-compose up

in the terminal to start a local HAPI FHIR server. This can take a few minutes, or longer if this is the first run.

After startup, the FHIR API can be accessed on <http://localhost:8080/fhir> (you can navigate to <http://localhost:8080> for some server overview and management tasks).

## Loading data

You can load data on the server using the FHIR API. Easiest is to do a POST on <http://localhost:8080/fhir> with a `transaction` or `batch` Bundle.

## Removing data

In true Docker fashion, you can always just throw away the container and recreate it if you want to clean the server. You can also use the [FHIR API to selectively delete data](https://smilecdr.com/docs/fhir_repository/deleting_data.html). The server is configured to support the HAPI `$expunge` operation.

## Note about the configuration

Configuration of the server is done using the `config.yaml` file in this directory. There are a lot in interesting config options commented out which might be of interest for your specific use case, so have a look there if you miss something.

The config is aimed at local testing, and for this reason a simple file based database within the container is used. For more scalability, a dedicated MySQL container or similar would be needed.

If there's a need to load packages, they should be set using the `implementationguides` key in `config.yaml`. At the moment, the nl-core and zib2020 packages are included as an example.