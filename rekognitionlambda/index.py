#
# Lambda function to detect labels in image using Amazon Rekognition
#

import logging
import boto3
from botocore.exceptions import ClientError
import os
from urllib.parse import unquote_plus
from boto3.dynamodb.conditions import Key, Attr
import uuid
from PIL import Image

thumbBucket = os.environ['RESIZEDBUCKET']

# Set the minimum confidence for Amazon Rekognition

minConfidence = 50

"""MinConfidence parameter (float) -- Specifies the minimum confidence level for the labels to return. 
Amazon Rekognition doesn't return any labels with a confidence lower than this specified value. 
If you specify a value of 0, all labels are returned, regardless of the default thresholds that the 
model version applies."""

## Instantiate service clients outside of handler for context reuse / performance

# Constructor for our s3 client object
s3_client = boto3.client('s3')
# Constructor to create rekognition client object
rekognition_client = boto3.client('rekognition')
# Constructor for DynamoDB resource object
dynamodb = boto3.resource('dynamodb')

def handler(event, context):

    print("Lambda processing event: ", event)

    # For each message (photo) get the bucket name and key
    for record in event['Records']:
        ourBucket = record['s3']['bucket']['name']
        ourKey = record['s3']['object']['key']

        # For each bucket/key, retrieve labels
        generateThumb(ourBucket, ourKey)
        rekFunction(ourBucket, ourKey)

    return

def generateThumb(ourBucket, ourKey):

    # Clean the string to add the colon back into requested name
    safeKey = replaceSubstringWithColon(ourKey)

    # Define upload and download paths
    key = unquote_plus(safeKey)
    tmpkey = key.replace('/', '')
    download_path = '/tmp/{}{}'.format(uuid.uuid4(), tmpkey)
    upload_path = '/tmp/resized-{}'.format(tmpkey)

    # Download file from s3 and store it in Lambda /tmp storage (512MB avail)
    try:
        s3_client.download_file(ourBucket, key, download_path)
    except ClientError as e:
        logging.error(e)
    # Create our thumbnail using Pillow library
    resize_image(download_path, upload_path)

    # Upload the thumbnail to the thumbnail bucket
    try:
        s3_client.upload_file(upload_path, thumbBucket, safeKey)
    except ClientError as e:
        logging.error(e)

    # Be good little citizens and clean up files in /tmp so that we don't run out of space
    os.remove(upload_path)
    os.remove(download_path)

    return

def resize_image(image_path, resized_path):
    with Image.open(image_path) as image:
        image.thumbnail(tuple(x / 2 for x in image.size))
        image.save(resized_path)

def rekFunction(ourBucket, ourKey):
    
    # Clean the string to add the colon back into requested name which was substitued by Amplify Library.
    safeKey = replaceSubstringWithColon(ourKey)
    
    print('Currently processing the following image')
    print('Bucket: ' + ourBucket + ' key name: ' + safeKey)

    detectLabelsResults = {}

    # Try and retrieve labels from Amazon Rekognition, using the confidence level we set in minConfidence var
    try:
        detectLabelsResults = rekognition_client.detect_labels(Image={'S3Object': {'Bucket':ourBucket, 'Name':safeKey}},
        MaxLabels=10,
        MinConfidence=minConfidence)

    except ClientError as e:
        logging.error(e)

    # Create our array and dict for our label construction

    objectsDetected = []

    imageLabels = {
        'image': safeKey
    }

    # Add all of our labels into imageLabels by iterating over response['Labels']

    for label in detectLabelsResults['Labels']:
        newItem = label['Name']
        objectsDetected.append(newItem)
        objectNum = len(objectsDetected)
        itemAtt = f"object{objectNum}"

        # We now have our shiny new item ready to put into DynamoDB
        imageLabels[itemAtt] = newItem


    # Instantiate a table resource object of our environment variable
    imageLabelsTable = os.environ['TABLE']
    table = dynamodb.Table(imageLabelsTable)

    # Put item into table
    try:
        table.put_item(Item=imageLabels)
    except ClientError as e:
        logging.error(e)

    return

# Clean the string to add the colon back into requested name
def replaceSubstringWithColon(txt):

    return txt.replace("%3A", ":")
