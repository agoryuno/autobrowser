FROM python:slim-bullseye

ARG CACHE=0

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
COPY ./browser/server /app/browser/server
COPY ./bin/start-vnc /app/bin/start-vnc
COPY ./bin/install-certs /app/bin/install-certs
COPY ./bin/cleanup /app/bin/cleanup
COPY requirements.txt /

# Install necessary dependencies
RUN apt update && apt install -y \
    curl \
    zip \
    gettext \
    bzip2 \
    xz-utils \
    libgtk-3-0 \
    libdbus-glib-1-2 \
    libasound2 \
    netcat-openbsd \
    xvfb \
    x11vnc \
    mawk \
    libnss3-tools \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/* && \
    pip install -r /requirements.txt && \
    chmod +x /app/bin/create-ssl-config && \
    chmod +x /app/bin/create-ssl-cert && \
    chmod +x /app/bin/install-firefox && \
    chmod +x /app/bin/install-extension && \
    chmod +x /app/bin/make-firefox-profile && \
    chmod +x /app/bin/make-extension && \
    chmod +x /app/bin/make-token && \
    chmod +x /app/bin/start-firefox && \
    chmod +x /app/bin/start-vnc && \
    chmod +x /app/bin/install-certs && \
    chmod +x /app/bin/cleanup && \
    /app/bin/create-ssl-config && \
    /app/bin/create-ssl-cert && \
    cp /app/browser/server/certs/cert.pem /usr/local/share/ca-certificates/autobrowser.crt && \
    /app/bin/install-firefox && \
    echo "PROFILE_ID=$(tr -dc 'a-z' < /dev/urandom | head -c1)$(tr -dc 'a-z0-9' < /dev/urandom | head -c7)" > /etc/profile.d/profile_id.sh && \
    chmod +x /etc/profile.d/profile_id.sh

# Load environment variables
SHELL ["/bin/bash", "-c", "-l"]

# Then source the environment variables explicitly before each RUN command that needs them
RUN source /etc/profile.d/profile_id.sh && \
    /app/bin/make-firefox-profile $PROFILE_ID && \
    update-ca-certificates && \
    /app/bin/install-extension $PROFILE_ID && \
    /app/bin/install-certs $PROFILE_ID && \
    /app/bin/cleanup && \
    apt purge -y \
    curl \
    zip \
    bzip2 \
    xz-utils && \
    apt autoremove -y

EXPOSE 443

ENV DISPLAY=:99
CMD ["/app/bin/start-vnc"]