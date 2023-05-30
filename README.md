# Autobrowser

An alternative to a webdriver: Firefox Developer Edition running in a Docker container with a simple control API.

Can't be easily detected as a robot by websites.

Ultimately meant as a browser for LLMs.

# Installing

To install this service you need to have Docker installed.

1. Clone the repository:

```bash
git clone https://github.com/agoryuno/autobrowser.git
```

2. Copy the 'base-config.ini' file and rename the copy to 'config.ini'. Inside the file,
in the "FIREFOX" section, fill in the value of the "VNC_PASS" setting. This will be the 
password for the VNC instance and it should be at most 8 characters long and contain only
alphanumerics

3. Inside the project directory execute:

```bash
./build-service
```

You might need super-user privileges to run this command.

# Running

The service can be started with

```bash
./run-service
```

(may require super-user privileges) from inside the project's root directory.

# TLS certificate

The service will generate its own TLS certificate when building the Docker image
but you can provide a ceritificate issued by a trusted authority. Copy the certificate's files into the `./bin/certificate/ directory.

Make sure the certificate files are named:

* cert.pem - certificate
* key.pem - private key
