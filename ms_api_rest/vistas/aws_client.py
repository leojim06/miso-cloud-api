import boto3
from flask import current_app

def aws_session():
    return boto3.Session(
        aws_access_key_id=current_app.config['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=current_app.config['AWS_SECRET_ACCESS_KEY']
    )

def s3_client():
    return aws_session().client('s3')

def sqs_client():
    return aws_session().client('sqs', region_name="us-east-1")



def upload_file_to_s3(file=None, filename=None):
    try:
        s3 = s3_client()
        s3.upload_fileobj(
            file,
            current_app.config['BUCKET_NAME'],
            'files/upload/{}'.format(filename),
        )
        return True
    except Exception as ex:
        print(f'No se pudo subir el archivo a S3: {ex}')
        return False

def delete_file_from_s3(file_key=None):
    try:
        s3 = s3_client()
        s3.delete_object(
            Bucket=current_app.config['BUCKET_NAME'],
            Key=file_key
        )
        return True
    except Exception as ex:
        print(f'No se pudo subir el archivo a S3: {ex}')
        return False

def send_message_to_sqs(message=None):
    try:
        sqs = sqs_client()
        response = sqs.send_message(
            QueueUrl=current_app.config['SQS_URL'],
            DelaySeconds=1,
            MessageBody=message
        )
        return True
    except Exception as ex:
        print(f'No se pudo subir el archivo a S3: {ex}')
        return False 