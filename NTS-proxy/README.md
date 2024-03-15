
# NTS proxy

A HTTP proxy specifically for handling authentication on the Nationale Terminologieserver.

## To start
The proxy is an addon for [mitmproxy](https://mitmproxy.org/). The simplest way to run it is using Docker:
> docker-compose up

Alternatively, you can install mitmproxy and invoke one of the commands using the `-s NTS-proxy.py` flag.

## To use
- Set the username and password to the Nationale Terminologieserver in the environment variables NTS_USER and NTS_PASS
- Set the proxy for the application to localhost:8080
- Tell the application to use http://terminologieserver/fhir as the base of the terminology server. Yes, http, not https! (You can use https, but it requires you to install the certificate according to [the instructions provided by mitmproxy](https://docs.mitmproxy.org/archive/v8/overview-getting-started/#configure-your-browser-or-device).

For the HL7 Validator, this would amount to:
>  java -jar validator_cli.jar -proxy localhost:8080 -tx http://terminologieserver.nl/fhir