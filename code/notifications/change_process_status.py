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
sns = boto3.client('sns')

def lambda_handler(event, context):
    TABLE_JOBS = os.environ['TABLE_JOBS']
    BUCKET_NAME = os.environ['BUCKET_NAME']
    EXPIRATION = int(os.environ['EXPIRATION'])
    TOPIC_ARN = os.environ['TOPIC_ARN']
    #print(json.dumps(event))
    try:
        records = event['Records']
        for record in records:
            if 'NewImage' in record['dynamodb'] and 'job_status' in record['dynamodb']['NewImage'] and record['dynamodb']['NewImage']['job_status']['S']=="complete":
                url = s3.generate_presigned_url('get_object',
                                                    Params={'Bucket': BUCKET_NAME,
                                                            'Key': record['dynamodb']['NewImage']['job_validated_file']['S']},
                                                    ExpiresIn=EXPIRATION)
                response = sns.publish(
                    TopicArn=TOPIC_ARN,
                    Message=url,
                    Subject='Validated file: '+ record['dynamodb']['NewImage']['job_id']['S']
                )
                
                print(response)
                print("Completed job:")
                print(json.dumps(record))
        return True
    except Exception as e:
        print(e)
        raise e