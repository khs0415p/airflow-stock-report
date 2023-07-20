FROM --platform=linux/arm64 ubuntu:20.04
LABEL title="stock-airflow"

ENV AIRFLOW_HOME="/home/airflow/"
ENV AIRFLOW_USER_HOME="/home/airflow/"
ENV MYSQL_HOST="airflow-db"
ENV MYSQL_USER="airflow"
ENV MYSQL_PASSWORD="airflow"
ENV AIRFLOW__DATABASE__SQL_ALCHEMY_CONN="mysql+mysqldb://${MYSQL_USER}:${MYSQL_PASSWORD}@${MYSQL_HOST}/airflow"
ENV AIRFLOW__CORE__LOAD_EXAMPLES="false"
ENV AIRFLOW__CORE__EXECUTOR="LocalExecutor"
ENV AIRFLOW__LOGGING__BASE_LOG_FOLDER="/home/airflow/logs"
ENV AIRFLOW__SCHEDULER__CHILD_PROCESS_LOG_DIRECTORY="/home/airflow/logs/scheduler"
ARG DEBIAN_FRONTEND=noninteractive

COPY requirements.txt ${AIRFLOW_HOME}
COPY script/entrypoint.sh /entrypoint.sh
COPY config/airflow.cfg ${AIRFLOW_HOME}
COPY dags/ ${AIRFLOW_HOME}

RUN apt-get update && apt-get install -y software-properties-common
RUN apt-get install -y python3-pip
RUN apt-get install -y vim
RUN apt-get install -y python3-dev default-libmysqlclient-dev build-essential
RUN apt-get install -y pkg-config
RUN apt-get install -y wget
RUN apt-get install unzip
RUN add-apt-repository ppa:ubuntu-mozilla-security/ppa && apt-get update
RUN apt-get -y install firefox
RUN wget https://github.com/mozilla/geckodriver/releases/download/v0.33.0/geckodriver-v0.33.0-linux-aarch64.tar.gz
RUN tar -xvzf geckodriver-v0.33.0-linux-aarch64.tar.gz
RUN rm geckodriver-v0.33.0-linux-aarch64.tar.gz
RUN mv ./geckodriver /usr/bin/geckodriver

WORKDIR ${AIRFLOW_USER_HOME}

RUN pip install -r requirements.txt

EXPOSE 8080 8793 5555
ENTRYPOINT [ "sh", "/entrypoint.sh" ]
CMD ["webserver"]