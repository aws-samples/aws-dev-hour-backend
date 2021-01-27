#
# Lambda function to detect labels in image using Amazon Rekognition
#

import logging
import boto3
from botocore.exceptions import ClientError
import os
from urllib.parse import unquote_plus
from boto3.dynamodb.conditions import Key, Attr

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
        rekFunction(ourBucket, ourKey)

    return

def rekFunction(ourBucket, ourKey):
    
    # Clean the string to add the colon back into requested name which was substitued by Amplify Library.
    safeKey = replaceSubstringWithColon(ourKey)
    
    print('Currently processing the following image')
    print('Bucket: ' + ourBucket + ' key name: ' + safeKey)

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
