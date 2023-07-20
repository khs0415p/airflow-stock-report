#! usr/bin/bash

 : "${AIRFLOW__CORE__FERNET_KEY:=${FERNET_KEY:=$(python3 -c "from cryptography.fernet import Fernet; FERNET_KEY = Fernet.generate_key().decode(); print(FERNET_KEY)")}}"

 
export \
 AIRFLOW__CORE__SQL_ALCHEMY_CONN \
 AIRFLOW__CORE__LOAD_EXAMPLES \
 AIRFLOW__CORE__EXECUTOR \
 AIRFLOW__CORE__FERNET_KEY \
 AIRFLOW__SCHEDULER__CHILD_PROCESS_LOG_DIRECTORY \
 AIRFLOW__LOGGING__BASE_LOG_FOLDER


case "$1" in
  webserver)
    airflow db init
    airflow users create --username admin --password admin --firstname admin \
            --lastname admin --role Admin --email admin@admin.com
    airflow scheduler & exec airflow webserver
    ;;
  *)
    exec "$@"
    ;;
esac
