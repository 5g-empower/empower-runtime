## build : docker build -t empower-runtime .
## run :   docker run --net=host --rm --privileged -it empower-runtime

FROM ubuntu:19.10
MAINTAINER Roberto Riggio <rriggio@fbk.eu>

# Installing python dependencies
RUN apt update
RUN apt -y install python3-pip wget unzip
RUN pip3 install tornado==6.0.3 construct==2.9.45 pymodm==0.4.1 influxdb==5.2.3

# Fetching the latest repository from empower-runtime
RUN wget https://github.com/5g-empower/empower-runtime/archive/master.zip
RUN unzip master.zip
RUN rm master.zip
RUN ln -sf /empower-runtime-master/conf/ /etc/empower
RUN mkdir -p /var/www/
RUN ln -s /empower-runtime-master/webui/ /var/www/empower

# Run the controller
ENTRYPOINT ["python3.7", "/empower-runtime-master/empower-runtime.py"]

# Expose Web GUI
EXPOSE 8888

# Expose LVAPP Server
EXPOSE 4433

# Expose VBSP Server
EXPOSE 5533
