import boto3
import json
import os

# Create a DynamodDB client outside of the handler function so we can reuse the
# clients between invocations. For more information on Boto3 client, see:
# https://boto3.amazonaws.com/v1/documentation/api/latest/guide/clients.html
dynamodb_client = boto3.resource('dynamodb')

def handler(event, context):
    """
    An HTTP API integration that will return all personas in the database.

    Args:
        event (dict): The event that triggered the Lambda function
        context (dict): The context in which the Lambda function was called

    Returns:
        dict: A 200 response with a list of personas in the body.
    """

    try:
        # Gets all personas from the database
        table = dynamodb_client.Table(os.environ['TABLE_NAME'])
        personas = table.scan()

        # Format the response
        response = {
            'statusCode': 200,
            'body': personas['Items']
        }

        # Return a 200 response
        return {
            'statusCode': 200,
            'body': json.dumps(response)
        }
    except Exception as e:
        print(e)
        return {
            'statusCode': 500,
            'body': json.dumps({ 'message': 'Error processing message' })
        }