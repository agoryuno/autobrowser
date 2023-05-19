# Use an Ubuntu base image
FROM ubuntu:latest

ARG CACHE=0

# Install necessary dependencies
RUN apt-get update && apt-get install -y \
    curl \
    tar \
    bzip2 \
    python3 \
    python3-pip \
    libgtk-3-0 \
    libdbus-glib-1-2 \
    libxt6

# Install Flask
RUN pip3 install flask

# Set the working directory
WORKDIR /app

# Copy the scripts into the Docker image
COPY ./bin/install-firefox /app/bin/install-firefox
COPY ./bin/install-extension /app/bin/install-extension
COPY ./bin/make-firefox-profile /app/bin/make-firefox-profile
COPY ./bin/make-extension /app/bin/make-extension
COPY ./bin/create-ssl-config /app/bin/create-ssl-config
COPY ./bin/create-ssl-cert /app/bin/create-ssl-cert
COPY ./config.ini /app/config.ini
COPY ./bin/default-profile.tar.xz /app/bin/default-profile.tar.xz
COPY ./browser/extension /app/browser/extension

RUN mkdir -p .temp
COPY .temp /app/.temp

# Make the scripts executable
RUN chmod +x /app/bin/create-ssl-config
RUN chmod +x /app/bin/create-ssl-cert
RUN chmod +x /app/bin/install-firefox
RUN chmod +x /app/bin/install-extension
RUN chmod +x /app/bin/make-firefox-profile
RUN chmod +x /app/bin/make-extension

# Install extra packages
RUN apt-get install -y gettext
RUN apt-get install -y zip

# Run the scripts
RUN /app/bin/create-ssl-config
RUN /app/bin/create-ssl-cert

RUN if [ "$CACHE" = "1" ]; then \
        echo "Installing Firefox from cache download..."; \
        /app/bin/install-firefox -c .temp; \
    else \
        echo "Downloading Firefox"; \
        /app/bin/make-firefox; \
    fi
RUN /app/bin/install-firefox

# Copy your Flask application into the Docker image
COPY ./browser/server /app/browser/server

# Expose the port your Flask app runs on
EXPOSE 5000

# Run the Flask server
CMD ["python3", "/app/browser/server/app.py"]
