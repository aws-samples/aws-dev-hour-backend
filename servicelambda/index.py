#
# # s3 Image Rekognition Front End Microservice
#

import logging
import boto3
from botocore.exceptions import ClientError
import os


# Constructors for Amazon DynamoDB and S3 resource object
dynamodb = boto3.resource('dynamodb')
s3 = boto3.resource('s3')

def handler(event, context):

    # Detect requested action from the Amazon API Gateway Event
    action = event['action']
    image = event['key']
    
    imageRequest = {
    "key": image
    }
    
    # GET Request from API
    if action == "getLabels":
        getResults = getLabelsFunction(imageRequest)
        if "image" in getResults:
            return getResults
        else:
            return "No Results"

    # DELETE Request from API
    if action == "deleteImage":
        delResults = deleteImage(imageRequest)
        return delResults
    else:
        raise Exception("Action not detected or recognised")

def getLabelsFunction(image):

    key = image['key']

    # Instantiate a table resource object
    imageLabelsTable = os.environ['TABLE']
    table = dynamodb.Table(imageLabelsTable)

    # Get item from table

    try:
        response = table.get_item(Key={'image': key})
        item = response['Item']
        return item
        
    except ClientError as e:
        logging.error(e)
        return "No labels or error"

def deleteImage(image):

    key = image['key']

    # Instantiate a table resource object
    imageLabelsTable = os.environ['TABLE']
    table = dynamodb.Table(imageLabelsTable)

    # Delete item from table

    try:
        table.delete_item(Key={'image': key})

    except ClientError as e:
        logging.error(e)

    bucketName = os.environ["BUCKET"]
    resizedBucketName = os.environ["RESIZEDBUCKET"]

    # Delete Photo and Thumbnail from Amazon S3

    try:
        s3.Object(bucketName, key).delete()
        s3.Object(resizedBucketName, key).delete()

    except ClientError as e:
        logging.error(e)

    return "Delete request successfully processed"