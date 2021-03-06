FROM debian:stretch

# Basic setup
RUN apt-get update \
    && apt-get install -y \
    build-essential \
    python3-dev \
    python3-pip \
    python3-cffi \
    python3-cryptography \
    wget \
    supervisor \
    nano \
    git \
    curl

# Get gcloud manually, since we use gcloud beta commands:
RUN curl -sSL https://sdk.cloud.google.com > /tmp/gcl \
    && bash /tmp/gcl --install-dir=/root/gcloud --disable-prompts
ARG gcloud_bin=/root/gcloud/google-cloud-sdk/bin
ENV PATH "$PATH:"${gcloud_bin}
ENV GCLOUD=${gcloud_bin}/gcloud
RUN "${gcloud_bin}"/gcloud components install beta --quiet

# Install redis for queueing
RUN curl -o /tmp/redis-stable.tar.gz http://download.redis.io/redis-stable.tar.gz \
  && cd /tmp \
  && tar -zxf redis-stable.tar.gz \
  && cd redis-stable \
  && make \
  && make install \
  && cp redis.conf /etc/redis.conf

# Pull the source code:
ARG appdir=/www
RUN mkdir ${appdir} \
  && git clone https://github.com/blawney/cloud-transfer-rest ${appdir}

# Install the python dependencies, as given from the repository:
RUN pip3 install --no-cache-dir -r "${appdir}"/requirements.txt
ENV APP_ROOT="${appdir}"

# Copy the startup script
RUN mkdir /opt/startup
ADD startup_commands.sh /opt/startup/

ENTRYPOINT ["/bin/bash"]
