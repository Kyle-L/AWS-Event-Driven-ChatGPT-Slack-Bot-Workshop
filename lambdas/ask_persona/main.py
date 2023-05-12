import boto3
import json
import os
import openai

# Create a DynamodDB and SQS clients outside of the handler function so we can reuse the
# clients between invocations. For more information on Boto3 clients, see:
# https://boto3.amazonaws.com/v1/documentation/api/latest/guide/clients.html
dynamodb_client = boto3.resource('dynamodb')
ssm_client = boto3.client('ssm')

# Global variables
OPENAI_API_KEY = ssm_client.get_parameter(Name=os.environ['SSM_OPENAI_API_KEY'], WithDecryption=True)['Parameter']['Value']

# Set OpenAI API key from Parameter Store
openai.api_key = OPENAI_API_KEY

def handler(event, context):
    """
    An HTTP API integration that will process a user prompt with a persona.

    Args:
        event (dict): The event that triggered the Lambda function
        context (dict): The context in which the Lambda function was called

    Returns:
        dict: A 200 response with the response from OpenAI in the body.
    """

    try:
        # Get the body of the request
        body = json.loads(event['body'])

        # Get the name of the persona
        name = body['name']
        question = body['question']

        # Gets the persona from the database
        table = dynamodb_client.Table(os.environ['TABLE_NAME'])
        persona = table.get_item(
            Key={
                'name': name
            }
        )
        person_body = persona['Item']['persona']

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                "role": "system",
                "content": person_body
            },
            {
                "role": "user",
                "content": question
            }
            ],
            max_tokens=150,
        )
            

        # Return a 200 response
        return {
            'statusCode': 200,
            'body': json.dumps({ 'message': response['choices'][0]['message']['content'] } )
        }
    except Exception as e:
        print(e)
        return {
            'statusCode': 500,
            'body': json.dumps({ 'message': 'Error processing message' })
        }