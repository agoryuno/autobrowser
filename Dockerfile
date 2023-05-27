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
    #libxt6 \
    libasound2 \
    netcat-openbsd \
    #libxtst6 \
    #libx11-xcb1 \
    xvfb \
    x11vnc \
    mawk \
    libnss3-tools \
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
COPY ./browser/server /app/browser/server
COPY ./bin/start-vnc /app/bin/start-vnc
COPY ./bin/install-certs /app/bin/install-certs


#RUN mkdir -p .temp
#COPY .temp /app/.temp

# Make the scripts executable
RUN chmod +x /app/bin/create-ssl-config
RUN chmod +x /app/bin/create-ssl-cert
RUN chmod +x /app/bin/install-firefox
RUN chmod +x /app/bin/install-extension
RUN chmod +x /app/bin/make-firefox-profile
RUN chmod +x /app/bin/make-extension
RUN chmod +x /app/bin/make-token
RUN chmod +x /app/bin/start-firefox
RUN chmod +x /app/bin/start-vnc
RUN chmod +x /app/bin/install-certs

# Run the scripts
RUN /app/bin/create-ssl-config
RUN /app/bin/create-ssl-cert
RUN cp /app/browser/server/certs/cert.pem /usr/local/share/ca-certificates/autobrowser.crt

RUN /app/bin/install-firefox

RUN echo "PROFILE_ID=$(tr -dc 'a-z' < /dev/urandom | head -c1)$(tr -dc 'a-z0-9' < /dev/urandom | head -c7)" > /etc/profile.d/profile_id.sh && \
    chmod +x /etc/profile.d/profile_id.sh

# Load environment variables
SHELL ["/bin/bash", "-c", "-l"]

# Then source the environment variables explicitly before each RUN command that needs them
RUN source /etc/profile.d/profile_id.sh
RUN echo $PROFILE_ID

RUN /app/bin/make-firefox-profile $PROFILE_ID
RUN update-ca-certificates
RUN /app/bin/install-extension

# Add the certificate to Firefox
RUN /app/bin/install-certs $PROFILE_ID

# Remove Firefox download cache
RUN rm -rf /app/.temp/
RUN rm -rf /app/browser/extension/
RUN rm -f /app/bin/default-profile.tar.xz

# Purge unneeded packages
RUN apt purge -y \
    zip \
    bzip2 \
    xz-utils 
    #libnss3-tools 
RUN apt autoremove -y

EXPOSE 443

ENV DISPLAY=:99
CMD ["/app/bin/start-vnc"]