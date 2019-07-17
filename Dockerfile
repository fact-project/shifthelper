FROM ubuntu:16.04 as builder

RUN apt update && apt install build-essential curl --yes \
	&& rm -rf /var/lib/apt/lists/*

RUN curl -Lo miniconda.sh https://repo.continuum.io/miniconda/Miniconda3-4.4.10-Linux-x86_64.sh \
  && bash miniconda.sh -b -p /opt/miniconda \
  && /opt/miniconda/bin/conda install \
  	pip \
  	nomkl \
	python=3.6 \
	pandas=0.22.0 \
	numpy=1.14.1 \
	matplotlib=2.1 \
	python-dateutil=2.6.1 \
	sqlalchemy=1.2.4 \
	PyMySQL=0.8.0 \
	requests=2.18.4 \
	docopt=0.6.2 \
	pytz=2018.3 \
	numexpr=2.6.4 \
	scipy=1.0.0 \
	&& /opt/miniconda/bin/conda clean --all --yes \
	&& rm miniconda.sh \
	&& ln -s /opt/miniconda/etc/profile.d/conda.sh /etc/profile.d/conda.sh

RUN mkdir /opt/shifthelper
COPY setup.py /opt/shifthelper/
COPY shifthelper /opt/shifthelper/shifthelper
RUN /opt/miniconda/bin/pip install /opt/shifthelper \
	&& rm -rf ~/.cache/pip

# start again and copy only the needed stuff (no gcc and so on)
FROM ubuntu:16.04

COPY --from=builder  /opt/ /opt/

RUN apt clean && apt update && apt install -y --no-install-recommends locales && rm -rf /var/lib/apt/lists/*
RUN locale-gen en_US.UTF-8
ENV LC_ALL='en_US.UTF-8'
RUN useradd --create-home --uid 1064 --user-group factshifthelper
COPY run.sh /home/factshifthelper
USER factshifthelper
CMD /home/factshifthelper/run.sh
