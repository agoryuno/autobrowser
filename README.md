# Autobrowser

An alternative to a webdriver: Firefox Developer Edition running in a Docker container with a simple control API.

Can't be easily detected as a robot by websites.

Ultimately meant as a browser for LLMs.

# Installing

To install this service you need to have Docker installed.

Clone the repository:

```git clone https://github.com/agoryuno/autobrowser.git```

Inside the project directory execute:

```./build-service```

You might need super-user privileges to run this command.

# Running

The service can be started with

```./run-service```

(may require super-user privileges) from inside the project's root directory.

# TLS certificate

The service will generate its own TLS certificate when building the Docker image
but you can provide a ceritificate issued by a trusted authority. Copy the certificate's files into the `./bin/certificate/ directory.

Make sure the certificate files are named:

* cert.pem - certificate
* key.pem - private key
