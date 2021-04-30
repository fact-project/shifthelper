FROM ubuntu:20.04 as builder

RUN apt update && apt install build-essential curl --yes \
	&& rm -rf /var/lib/apt/lists/*

RUN curl -Lo miniconda.sh https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh \
  && bash miniconda.sh -b -p /opt/miniconda \
  && /opt/miniconda/bin/conda install \
  	pip \
  	nomkl \
	python=3.8 \
	pandas \
	numpy \
	matplotlib \
	python-dateutil \
	sqlalchemy \
	PyMySQL \
	requests \
	docopt \
	pytz \
	numexpr \
	scipy \
	&& /opt/miniconda/bin/conda clean --all --yes \
	&& rm miniconda.sh \
	&& ln -s /opt/miniconda/etc/profile.d/conda.sh /etc/profile.d/conda.sh

RUN mkdir /opt/shifthelper
COPY setup.py /opt/shifthelper/
COPY shifthelper /opt/shifthelper/shifthelper
RUN /opt/miniconda/bin/pip install /opt/shifthelper \
	&& rm -rf ~/.cache/pip

# start again and copy only the needed stuff (no gcc and so on)
FROM ubuntu:20.04

COPY --from=builder  /opt/ /opt/

RUN apt clean && apt update && apt install -y --no-install-recommends locales && rm -rf /var/lib/apt/lists/*
RUN locale-gen en_US.UTF-8
ENV LC_ALL='en_US.UTF-8'
RUN useradd --create-home --uid 1064 --user-group factshifthelper
COPY run.sh /home/factshifthelper
USER factshifthelper
CMD /home/factshifthelper/run.sh
