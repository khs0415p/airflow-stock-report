from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from crawl.report_crawling import crawling
from utils import db_check
import pendulum
import platform

_platform = platform.system()
if _platform == "Darwin":
    from _scproxy import _get_proxy_settings
    _get_proxy_settings()

kst = pendulum.timezone("Asia/Seoul")

deafult_args = {
    "owner" : "Hyunsoo",
    "email_on_failure": False,
    "provide_context": True,
}

with DAG(
    dag_id="stock-crawl-process",
    default_args=deafult_args,
    description="Data(stock) crawling and Data pre-processing",
    start_date=datetime(2023, 7, 1, tzinfo=kst),
    schedule="@weekly",
    tags=["crawling"],
) as dag:
    
    # db check
    t1 = PythonOperator(
        task_id = "db-check",
        python_callable=db_check,
        retries=3,
        retry_delay=timedelta(minutes=5),
    )
    
    # crawling (db 저장)
    t2 = PythonOperator(
        task_id = "crawling",
        python_callable=crawling,
        retries=3,
        retry_delay=timedelta(minutes=5),
        depends_on_past=True
    )
    
    t1 >> t2