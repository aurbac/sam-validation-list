import json
import urllib.parse
import boto3
from botocore.exceptions import ClientError
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all
import os
import io
import csv
import datetime

patch_all()

s3 = boto3.client('s3')
dynamodb = boto3.client('dynamodb')

def lambda_handler(event, context):
    TABLE_JOBS = os.environ['TABLE_JOBS']
    #print(json.dumps(event))
    try:
        records = event['Records']
        for record in records:
            if 'NewImage' in record['dynamodb'] and 'job_status' in record['dynamodb']['NewImage'] and record['dynamodb']['NewImage']['job_status']['S']=="complete":
                print("Completed job:")
                print(json.dumps(record))
        return True
    except Exception as e:
        print(e)
        raise e