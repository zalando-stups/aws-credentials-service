FROM registry.opensource.zalan.do/stups/python:latest

COPY requirements.txt /
RUN pip3 install -r /requirements.txt

COPY app.py /
COPY swagger.yaml /

# Publish API specification (https://opensource.zalando.com/restful-api-guidelines/#192)
COPY swagger.yaml /zalando-apis/

WORKDIR /data
CMD /app.py
