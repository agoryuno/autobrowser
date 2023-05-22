FROM python:slim-bullseye

ARG CACHE=0

# Install necessary dependencies
RUN apt update && apt install -y \
    curl \
    zip \
    gettext \
    bzip2 \
    xz-utils \
    libgtk-3-0 \
    libdbus-glib-1-2 \
    libxt6 \
    libasound2 \
    netcat-openbsd \
    libxtst6 \
    libx11-xcb1 \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

#RUN apk add openssl zip curl python

COPY requirements.txt /

RUN pip install -r /requirements.txt

# Set the working directory
WORKDIR /app

# Copy the scripts into the Docker image
COPY ./bin/install-firefox /app/bin/install-firefox
COPY ./bin/install-extension /app/bin/install-extension
COPY ./bin/make-firefox-profile /app/bin/make-firefox-profile
COPY ./bin/make-extension /app/bin/make-extension
COPY ./bin/create-ssl-config /app/bin/create-ssl-config
COPY ./bin/create-ssl-cert /app/bin/create-ssl-cert
COPY ./bin/make-token /app/bin/make-token
COPY ./config.ini /app/config.ini
COPY ./bin/default-profile.tar.xz /app/bin/default-profile.tar.xz
COPY ./browser/extension /app/browser/extension
COPY ./bin/start-firefox /app/bin/start-firefox
# Copy your Flask application into the Docker image
COPY ./browser/server /app/browser/server

RUN mkdir -p .temp
COPY .temp /app/.temp

# Make the scripts executable
RUN chmod +x /app/bin/create-ssl-config
RUN chmod +x /app/bin/create-ssl-cert
RUN chmod +x /app/bin/install-firefox
RUN chmod +x /app/bin/install-extension
RUN chmod +x /app/bin/make-firefox-profile
RUN chmod +x /app/bin/make-extension
RUN chmod +x /app/bin/make-token

# Run the scripts
RUN /app/bin/create-ssl-config
RUN /app/bin/create-ssl-cert
RUN /app/bin/install-firefox

# Remove Firefox download cache
RUN rm -rf /app/.temp

# Expose the port your Flask app runs on
EXPOSE 5000

# Run the Flask server
CMD ["/app/bin/start-firefox"]