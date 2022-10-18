FROM ubuntu:20.04

RUN apt update \
	&& apt install --yes --no-install-recommends \
		locales python3 python3-pip python3-wheel python3-setuptools \
	&& echo "en_US.UTF-8 UTF-8" > /etc/locale.gen \
	&& locale-gen \
	&& python3 -m pip install --no-cache poetry==1.1.6 \
	&& rm -rf /var/lib/apt/lists/*


ENV LC_ALL='en_US.UTF-8'
ENV LANG="en_US.UTF-8"

RUN mkdir /opt/shifthelper
WORKDIR /opt/shifthelper/
COPY pyproject.toml poetry.lock ./

# This will only install the depdendencies in poetry.lock,
# but we do this, so we don't have to run it with each build
RUN poetry config virtualenvs.create false \
	&& poetry install --no-dev

COPY shifthelper /opt/shifthelper/shifthelper
# need to run poetry a second time to also install shifthelper
RUN poetry config virtualenvs.create false \
	&& poetry install --no-dev

RUN useradd --create-home --uid 1064 --user-group factshifthelper
COPY run.sh /home/factshifthelper
USER factshifthelper
CMD /home/factshifthelper/run.sh
