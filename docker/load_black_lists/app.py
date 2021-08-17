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

def handler():
    TABLE_VALUES = os.environ['TABLE_VALUES']
    OBJECT_KEY = os.environ['OBJECT_KEY']
    BUCKET_NAME = os.environ['BUCKET_NAME']
    try:
        nows = datetime.datetime.now()
        print("Start: " + nows.strftime("%Y-%m-%d %H:%M:%S"))
        
        myTable = "black_lists_"+nows.strftime("%Y_%m_%d_%H_%M")
        
        table = dynamodbr.create_table(
            TableName=myTable,
            BillingMode='PAY_PER_REQUEST',
            AttributeDefinitions=[
                    {
                        'AttributeName': 'number',
                        'AttributeType': 'S'
                    },
            ],
            KeySchema=[
                { 'AttributeName': "number", 'KeyType': 'HASH' }
            ]
        )
        
        response = s3.get_object(Bucket=BUCKET_NAME, Key=OBJECT_KEY)
        df = pd.read_csv(io.BytesIO(response['Body'].read()), encoding='ISO-8859-1')
        
        table.meta.client.get_waiter('table_exists').wait(TableName=myTable)
        
        with table.batch_writer(overwrite_by_pkeys=['number']) as batch:
            for index, row in df.iterrows():
                batch.put_item(Item={ 'number': str(row[0]) })
        
        nowe = datetime.datetime.now()
        print("End: " + nowe.strftime("%Y-%m-%d %H:%M:%S"))
        
        response = dynamodb.update_item(
            TableName=TABLE_VALUES,
            Key={ 'key_name': { 'S': 'black_list_table' } },
            AttributeUpdates={ 'key_value': { 'Value': { 'S': myTable }, 'Action': 'PUT' } }
        )
        
        duration = nowe - nows
        print("Duration: " + str(duration))
        
        response = {
            "statusCode": 200,
            "body": json.dumps("Hola")
        }
        return response
    except Exception as e:
        print(e)
        raise e
        
handler()