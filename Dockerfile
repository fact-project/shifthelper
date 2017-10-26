FROM continuumio/miniconda3

RUN apt update && apt install build-essential --yes

RUN conda install \
	pandas requests numpy matplotlib \
	python-dateutil sqlalchemy PyMySQL \
	docopt pytz numexpr scipy pymongo astropy \
	&& conda clean --all --yes 

RUN mkdir /opt/shifthelper
COPY setup.py requirements.txt /opt/shifthelper/
COPY shifthelper /opt/shifthelper/shifthelper
RUN pip install -r /opt/shifthelper/requirements.txt && pip install /opt/shifthelper

RUN useradd --create-home --uid 1064 --user-group factshifthelper
COPY run.sh /home/factshifthelper
USER factshifthelper
CMD /home/factshifthelper/run.sh
