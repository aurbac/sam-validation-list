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

TEMP_FILE = '/tmp/validation.csv'

def lambda_handler(event, context):
    TABLE_JOBS = os.environ['TABLE_JOBS']
    TABLE_BLACK_LIST = os.environ['TABLE_BLACK_LIST']
    print(json.dumps(event))
    try:
        for record in event['Records']:
            objs = json.loads(record['body'])
            print(objs)
            
            # Recorre los registros de mensajes devueltos por SQS
            for rec in objs['Records']:
                print(json.dumps(rec))
                
                # extrae los datos del objeto creado en amazon s3
                object_key = rec['s3']['object']['key']
                bucket_name = rec['s3']['bucket']['name']
                
                # valida el tamño del archivo, si es mayor a 1MB es para proceso externo
                external_process = False
                if rec['s3']['object']['size']>1000000:
                    external_process = True
                
                # crea el registro de nuevo proceso en dynamodb
                nows = datetime.datetime.now()
                response = dynamodb.put_item(
                    TableName=TABLE_JOBS,
                    Item={
                        'job_id': { 'S': object_key },
                        'object_size': { 'N': str(rec['s3']['object']['size']) },
                        'job_status': { 'S': "in_progress" },
                        'external_process': { 'BOOL': external_process },
                        'job_started_at': { 'S': nows.strftime("%Y-%m-%d %H:%M:%S") }
                    }
                )
                
                # envia el proceso a amazon glue/ecs
                if external_process:
                    print("External process")
                # inicia el proceso en la funcion lambda
                else:
                    print("Lambda process")
                    # descarga el archivo creado en amazon s3
                    response = s3.get_object(Bucket=bucket_name, Key=object_key)
                    df = pd.read_csv(io.BytesIO(response['Body'].read()))
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
                    
                    dfr.to_csv(TEMP_FILE, index=False)
                    
                    s3r.Bucket(bucket_name).upload_file(TEMP_FILE,object_key+'-validated')
                    
                    nowe = datetime.datetime.now()
                    duration = nowe - nows
                    response = dynamodb.update_item(
                        TableName=TABLE_JOBS,
                        Key={
                            'job_id': { 'S': object_key }
                        },
                        AttributeUpdates={
                            'job_status': { 'Value': { 'S': 'complete' }, 'Action' : 'PUT' },
                            'job_ended_at' : { 'Value': { 'S': nowe.strftime("%Y-%m-%d %H:%M:%S") }, 'Action': 'PUT' },
                            'job_duration' : { 'Value': { 'S': str(duration) }, 'Action': 'PUT' },
                            'job_validated_file': { 'Value': { 'S': object_key+'-validated' }, 'Action': 'PUT' } 
                        }
                    )
                
        return True
    except Exception as e:
        print(e)
        raise e