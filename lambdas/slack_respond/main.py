import boto3
import json
import os
import openai
import urllib

# Create a DynamodDB and SQS clients outside of the handler function so we can reuse the
# clients between invocations. For more information on Boto3 clients, see:
# https://boto3.amazonaws.com/v1/documentation/api/latest/guide/clients.html
dynamodb_client = boto3.resource('dynamodb')
ssm_client = boto3.client('ssm')

# Global variables
SLACK_BOT_TOKEN = ssm_client.get_parameter(
    Name=os.environ['SSM_SLACK_TOKEN'], 
    WithDecryption=True
    )['Parameter']['Value']

OPENAI_API_KEY = ssm_client.get_parameter(
    Name=os.environ['SSM_OPENAI_API_KEY'], 
    WithDecryption=True
    )['Parameter']['Value']

MAX_OPENAI_TOKENS = int(os.environ['MAX_OPENAI_TOKENS'])

# Set OpenAI API key from Parameter Store
openai.api_key = OPENAI_API_KEY


def send_slack_message(channel_id, response_text):
    """
    Sends a message to a Slack channel using the chat.postMessage API method.

    Args:
        channel_id (str): The ID of the Slack channel to send the message to.
        response_text (str): The text of the message to send.
    """
    print("Messaging Slack...")

    # Slack API endpoint
    SLACK_URL = "https://slack.com/api/chat.postMessage"

    # Encode data for POST request
    data = urllib.parse.urlencode(
        (
            ("token", SLACK_BOT_TOKEN),
            ("channel", channel_id),
            ("text", response_text)
        )
    )
    data = data.encode("ascii")

    # Create POST request
    request = urllib.request.Request(SLACK_URL, data=data, method="POST")
    request.add_header( "Content-Type", "application/x-www-form-urlencoded" )

    # Send request
    urllib.request.urlopen(request).read()


def process(persona_name, prompt):
    """
    Processes a user prompt with a persona from our SQS queue, 
    finds the persona in DynamoDB, uses the persona to generate a response
    from OpenAI, and sends the response to Slack.

    Args:
        persona_name (str): The name of the persona to use.
        prompt (str): The user prompt to process.

    Returns:
        dict: A 200 response if the event is from a bot, None otherwise.

    Raises:
        e: Any exception raised by the function will be raised to the caller.
    """

    # Retrieve persona from DynamoDB
    table = dynamodb_client.Table(os.environ['TABLE_NAME'])
    persona = table.get_item(
        Key={
            'name': persona_name
        }
    )
    persona_body = persona['Item']['persona']

    # Generate response from OpenAI
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
            "role": "system",
            "content": persona_body
        },
        {
            "role": "user",
            "content": prompt
        }
        ],
        max_tokens=MAX_OPENAI_TOKENS,
    )

    # Extract response message from OpenAI API response
    return response['choices'][0]['message']['content']


def handler(event, context):
    """
    A trigger function to process a user prompt with a persona from our SQS queue,
    find the persona in DynamoDB, use the persona to generate a response
    from OpenAI, and send the response to Slack.

    Args:
        event (dict): The event that triggered the Lambda function
        context (dict): The context in which the Lambda function was called

    Returns:
        dict: A 200 response indicating that the message was sent successfully.
    
    Raises:
        e: Any exception raised by the function will be raised to the caller.
    """

    try:
        print("Eveent received. Processing...")

        # Printing the Slack event to the logs for debugging
        print(f"SQS event: {message}")

        # Retrieve message from SQS queue.
        # The message is a JSON object with the channel ID, text, and persona.
        # For more on SQS events, see:
        # https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html
        sqs_message = event['Records'][0]['body']
        message = json.loads(sqs_message)

        # Printing the Slack message to the logs for debugging
        print(f"SQS message: {message}")

        # Extract message data from SQS message
        channel_id = message['channel_id']
        text = message['text']
        persona_name = message['persona']

        # Process user prompt with persona and send response to Slack
        response = process(persona_name, text)
        send_slack_message(channel_id, response)

        # Return HTTP response
        return {
            'statusCode': 200,
            'body': json.dumps({ 'message': 'Message sent successfully' })
        }

    except Exception as e:
        print(e)
        return {
            'statusCode': 500,
            'body': json.dumps({ 'message': 'Error processing message' })
        }
