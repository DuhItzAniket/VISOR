ARG BASE_IMAGE
FROM ${BASE_IMAGE}
COPY visor.deb /fixture/visor.deb
RUN apt-get update \
    && apt-get install -y --no-install-recommends xvfb xauth fonts-dejavu-core \
    && apt-get satisfy -y --no-install-recommends "$(dpkg-deb --field /fixture/visor.deb Depends)" \
    && rm -rf /var/lib/apt/lists/*
COPY portable.tar.gz verify-clean-linux.sh /fixture/
ENTRYPOINT ["/bin/bash", "/fixture/verify-clean-linux.sh"]
