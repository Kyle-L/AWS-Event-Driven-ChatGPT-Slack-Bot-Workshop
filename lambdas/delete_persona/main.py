import boto3
import os
import json

# Create a DynamodDB client outside of the handler function so we can reuse the
# clients between invocations. For more information on Boto3 client, see:
# https://boto3.amazonaws.com/v1/documentation/api/latest/guide/clients.html
dynamodb_client = boto3.resource('dynamodb')

def handler(event, context):
    """
    An HTTP API integration that will delete a persona from the database.

    Args:
        event (dict): The event that triggered the Lambda function
        context (dict): The context in which the Lambda function was called

    Returns:
        dict: A 200 response indicating that the persona was deleted successfully.
    """

    try:
        # Get the person name from the path
        name = event['pathParameters']['name']

        # Delete the persona from the database
        table = dynamodb_client.Table(os.environ['TABLE_NAME'])
        table.delete_item(
            Key={
                'name': name
            }
        )

        # Return a 200 response
        return {
            'statusCode': 200,
            'body': json.dumps({ 'message': 'Persona deleted successfully' })
        }
    except Exception as e:
        print(e)
        return {
            'statusCode': 500,
            'body': json.dumps({ 'message': 'Error processing message' })
        }