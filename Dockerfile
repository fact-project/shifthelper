FROM continuumio/miniconda3



RUN conda install \
	pandas requests numpy matplotlib \
	python-dateutil sqlalchemy PyMySQL \
	docopt pytz numexpr scipy pymongo astropy 

RUN pip install twilio retrying wrapt \
	simple-crypt python-json-logger telepot \
	cachetools \
	pyfact==0.8.4 custos==0.0.7 \
	https://github.com/fact-project/smart_fact_crawler/archive/v0.2.2.tar.gz

RUN mkdir /opt/shifthelper
COPY setup.py /opt/shifthelper/
COPY shifthelper /opt/shifthelper/shifthelper
RUN pip install /opt/shifthelper

RUN useradd --create-home --uid 1064 --user-group factshifthelper
COPY run.sh /home/factshifthelper
USER factshifthelper
CMD /home/factshifthelper/run.sh
