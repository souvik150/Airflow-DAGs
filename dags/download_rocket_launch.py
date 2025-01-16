import json
import pathlib

import requests
from requests import exceptions as request_exceptions
import airflow
 
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

dag = DAG(
    dag_id='download_rocket_launch',
    start_date=airflow.utils.dates.days_ago(14),
    schedule_interval=None,
)

download_launches = BashOperator(
    task_id='download_launches',
    bash_command='curl -o /tmp/launches.json -L "https://ll.thespacedevs.com/2.2.0/launch/upcoming"',
    dag=dag,
)

def _get_pictures():
  #check if the directory exists
  pathlib.Path('/tmp/images').mkdir(parents=True, exist_ok=True)

  with open('/tmp/launches.json') as f:
    launches = json.load(f)
    image_urls = [launch['image'] for launch in launches['results']]
    for image_url in image_urls:
      try:
        response = requests.get(image_url)
        image_filename = image_url.split('/')[-1]
        with open(f'/tmp/images/{image_filename}', 'wb') as image_file:
          image_file.write(response.content)
        print(f"Downloaded {image_url} to /tmp/images")

      except request_exceptions.MissingSchema:
        print(f"{image_url} appears to be an invalid url")

      except request_exceptions.ConnectionError:
        print(f"Could not connect to {image_url}")

_get_pictures = PythonOperator(
    task_id='get_pictures',
    python_callable=_get_pictures,
    dag=dag,
)

notify = BashOperator(
    task_id='notify',
    bash_command='echo "There are now $(ls /tmp/images | wc -l) images."',
    dag=dag,
)

download_launches >> _get_pictures >> notify

