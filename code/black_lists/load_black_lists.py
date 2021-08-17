import json
import urllib.parse
import boto3
from botocore.exceptions import ClientError
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all
import os
import pandas as pd
import io
import csv
import datetime

patch_all()

s3 = boto3.client('s3')
s3r = boto3.resource('s3')
dynamodb = boto3.client('dynamodb')
ecs = boto3.client('ecs')

dynamodbr = boto3.resource('dynamodb')

def lambda_handler(event, context):
    TABLE_VALUES = os.environ['TABLE_VALUES']
    CLUSTER_NAME = os.environ['CLUSTER_NAME']
    TASK_DEFINITION = os.environ['TASK_DEFINITION']
    TASK_ROLE_ARN = os.environ['TASK_ROLE_ARN']
    SUBNET_ID_01 = os.environ['SUBNET_ID_01']
    SUBNET_ID_02 = os.environ['SUBNET_ID_02']
    SECURITY_GROUP_ID = os.environ['SECURITY_GROUP_ID']
    try:
        # Recorre los registros de mensajes devueltos por SQS
        for rec in event['Records']:

            # extrae los datos del objeto creado en amazon s3
            object_key = rec['s3']['object']['key']
            bucket_name = rec['s3']['bucket']['name']
            
            print(CLUSTER_NAME)
            
            response = ecs.run_task(
                cluster=CLUSTER_NAME,
                launchType='FARGATE',
                taskDefinition=TASK_DEFINITION.split('/')[1],
                overrides={
                    'containerOverrides': [
                        {   'name': 'container', 
                            'environment': [
                                { 'name': 'TABLE_VALUES', 'value': TABLE_VALUES },
                                { 'name': 'OBJECT_KEY', 'value': object_key },
                                { 'name': 'BUCKET_NAME', 'value': bucket_name }
                            ] 
                        
                        }
                    ],
                    'taskRoleArn':TASK_ROLE_ARN
                },
                networkConfiguration={
                    'awsvpcConfiguration': {
                                'subnets': [
                                    SUBNET_ID_01,SUBNET_ID_02
                                ],
                                'securityGroups': [
                                    SECURITY_GROUP_ID
                                ],
                                'assignPublicIp': 'ENABLED'
                            }
                }
            )
            
        return True
    except Exception as e:
        print(e)
        raise e