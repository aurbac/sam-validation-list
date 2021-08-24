import json
import urllib.parse
import boto3
from botocore.exceptions import ClientError
import os
import pandas as pd
import io
import csv
import datetime

s3 = boto3.client('s3')
s3r = boto3.resource('s3')
dynamodb = boto3.client('dynamodb')

dynamodbr = boto3.resource('dynamodb')

TEMP_FILE = '/tmp/validation.csv'
def handler():
    TABLE_JOBS = os.environ['TABLE_JOBS']
    TABLE_VALUES = os.environ['TABLE_VALUES']
    OBJECT_KEY = os.environ['OBJECT_KEY']
    BUCKET_NAME = os.environ['BUCKET_NAME']
    try:
        response = dynamodb.get_item(
            TableName=TABLE_VALUES,
            Key={
                'key_name' : { 'S' : "black_list_table" }
            }
        )
        print(response)
        
        if 'Item' in response:
            TABLE_BLACK_LIST = response['Item']['key_value']['S']
            nows = datetime.datetime.now()
            
            # descarga el archivo creado en amazon s3
            response = s3.get_object(Bucket=BUCKET_NAME, Key=OBJECT_KEY)
            df = pd.read_csv(io.BytesIO(response['Body'].read()), header=None, delimiter=',')
            #lines = df.to_dict('records')
            #print(lines)
            
            items = []
            
            for index, row in df.iterrows():
                
                response = dynamodb.get_item(
                    TableName=TABLE_BLACK_LIST,
                    Key={ 'number': { 'S': str(row[0]) } }
                )
                if not 'Item' in response:
                    items.append(row[0])
            
            dfr = pd.DataFrame(items)
            print("Resultado")
            print(dfr)
            
            dfr.to_csv(TEMP_FILE, index=False, header=None)
            
            s3r.Bucket(BUCKET_NAME).upload_file(TEMP_FILE,OBJECT_KEY+'-validated')
            
            nowe = datetime.datetime.now()
            duration = nowe - nows
            print(str(duration))
            response = dynamodb.update_item(
                TableName=TABLE_JOBS,
                Key={
                    'job_id': { 'S': OBJECT_KEY }
                },
                AttributeUpdates={
                    'job_status': { 'Value': { 'S': 'complete' }, 'Action' : 'PUT' },
                    'job_ended_at' : { 'Value': { 'S': nowe.strftime("%Y-%m-%d %H:%M:%S") }, 'Action': 'PUT' },
                    'job_duration' : { 'Value': { 'S': str(duration) }, 'Action': 'PUT' },
                    'job_validated_file': { 'Value': { 'S': OBJECT_KEY+'-validated' }, 'Action': 'PUT' } 
                }
            )
            print(response)
        else:
            print("No table black lists")
        return True
    except Exception as e:
        print(e)
        raise e
        
handler()