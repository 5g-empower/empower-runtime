## build : docker build -t empower-runtime .
## run :   docker run --net=host --rm --privileged -it empower-runtime

FROM python:3.7-alpine
MAINTAINER Roberto Riggio <rriggio@fbk.eu>
RUN pip3 install tornado construct pymodm influxdb

# Fetching the latest repository from empower-runtime.
RUN wget https://github.com/5g-empower/empower-runtime/archive/master.zip
RUN unzip master.zip
RUN rm master.zip
RUN ln -sf /empower-runtime-master/conf/ /etc/empower

# Run the controller
ENTRYPOINT ["/empower-runtime-master/empower-runtime.py"]

# Expose Web GUI
EXPOSE 8888

# Expose LVAPP Server
EXPOSE 4433

# Expose VBSP Server
EXPOSE 5533
