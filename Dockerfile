# Starting point
FROM ubuntu:16.04

# Install wget and python with dependencies
RUN apt-get -y update

RUN apt-get -y install python wget

RUN apt-get -y update

RUN apt-get -y upgrade python-dev

RUN apt-get -y install python3-pip

RUN pip3 install docopt  \
		  sevenbridges-python \
		  ruamel.yaml \
		  pyyaml

# add java ppa
RUN apt-get -y install software-properties-common && \
    apt-get -y install python-software-properties && \
    add-apt-repository ppa:webupd8team/java && \
    apt-get -y update 

# automatically accept oracle license
RUN echo oracle-java8-installer shared/accepted-oracle-license-v1-1 select true | /usr/bin/debconf-set-selections

# install java 8 oracle jdk
RUN apt-get -y install oracle-java8-installer && apt-get clean
RUN echo "JAVA_HOME=/usr/lib/jvm/java-8-oracle" >> /etc/environment

# cd to opt
WORKDIR /opt

# install rabix
RUN wget https://github.com/rabix/bunny/releases/download/v1.0.0/rabix-1.0.0.tar.gz && \
    tar -xvf rabix-1.0.0.tar.gz && rm rabix-1.0.0.tar.gz
ENV BUNNY /opt/rabix-cli-1.0.0/rabix


# copy files to docker
COPY Dockerfile /opt/
COPY cwl_decomposer.py /opt/
COPY import_cwl_to_sbg.py /opt/

# set maintainer
MAINTAINER Bogdan Gavrilovic, Seven Bridges Genomics, <bogdan.gavrilovic@sbgenomics.com>
