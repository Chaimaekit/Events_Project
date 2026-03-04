from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.hooks.base import BaseHook
from datetime import datetime, timedelta
import requests
import os
import sys

sys.path.insert(0, '/opt/airflow')

default_args = {
    'owner': 'evently',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

def run_indexing():
    from elastic.elastic_script import indexing
    result = indexing()
    if not result:
        raise ValueError("Indexing returned no results — possible scraping failure")
    return result

def send_slack_success(context):
    webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
    if not webhook_url:
        return
    requests.post(webhook_url, json={
        "text": f"*Evently scraping succeeded!*\nRun: `{context['ds']}`\nAll sources indexed successfully."
    })

def send_slack_failure(context):
    webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
    if not webhook_url:
        return
    exception = context.get('exception', 'Unknown error')
    requests.post(webhook_url, json={
        "text": f"*Evently scraping FAILED!!!!*\nRun: `{context['ds']}`\nError: `{exception}`\nCheck Airflow at http://localhost:8080"
    })

with DAG(
    dag_id='evently_daily_scraping',
    default_args=default_args,
    description='Daily scraping and indexing of Evently events',
    schedule_interval='0 0 * * *', 
    start_date=datetime(2026, 1, 1),
    catchup=False,
    on_success_callback=send_slack_success,
    on_failure_callback=send_slack_failure,
    tags=['evently', 'scraping']
) as dag:

    scrape_and_index = PythonOperator(
        task_id='scrape_and_index_events',
        python_callable=run_indexing,
    )
