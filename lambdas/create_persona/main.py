import boto3
import json
import os

# Create a DynamodDB client outside of the handler function so we can reuse the
# clients between invocations. For more information on Boto3 client, see:
# https://boto3.amazonaws.com/v1/documentation/api/latest/guide/clients.html
dynamodb_client = boto3.resource('dynamodb')

def handler(event, context):
    """
    An HTTP API integration that will create a persona in the database.

    Args:
        event (dict): The event that triggered the Lambda function
        context (dict): The context in which the Lambda function was called

    Returns:
        dict: A 200 response indicating that the persona was created successfully.
    """

    try:
        # Get the body of the request
        body = json.loads(event['body'])

        # Get the name of the persona
        name = body['name']
        persona_body = body['persona']

        # Create a new persona in the database
        table = dynamodb_client.Table(os.environ['TABLE_NAME'])
        table.put_item(
            Item={
                'name': name,
                'persona': persona_body
            }
        )

        # Return a 200 response
        return {
            'statusCode': 200,
            'body': json.dumps({ 'message': 'Persona created successfully' })
        }
    except Exception as e:
        print(e)
        return {
            'statusCode': 500,
            'body': json.dumps({ 'message': 'Error processing message' })
        }