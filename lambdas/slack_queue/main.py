import json
import boto3
import os

# Get the URL of the SQS queue from the environment variables
SQS_QUEUE_URL = os.environ['SQS_QUEUE_URL']

# Create an SQS client outside of the handler function so we can reuse the
# client between invocations. For more information on Boto3 clients, see:
# https://boto3.amazonaws.com/v1/documentation/api/latest/guide/clients.html
sqs_client = boto3.resource('sqs')


def handle_challenge(slack_event):
    """
    A function to check if the event is a challenge event from Slack
    so we can return the challenge value and verify the endpoint.
    For more information on challenge events, see:
    https://api.slack.com/events/url_verification

    Args:
        slack_event (dict): The event dictionary from the Slack event

    Returns:
        dict: A 200 response with the challenge value, if the event is a challenge event.
              None, otherwise.
    """
    challenge_value = slack_event.get("challenge", None)

    if challenge_value is not None:
        return {
            'statusCode': 200,
            'body': challenge_value
        }
    
    return None


def handle_bot(slack_event):
    """
    A function to check if the event is from a bot. If it is, we don't
    want to process it. We'll just return a 200 response.

    Args:
        slack_event (dict): The event dictionary from the Slack event

    Returns:
        dict: A 200 response if the event is from a bot, None otherwise.
    """
    is_bot_event = slack_event.get("event").get("bot_id", None) is not None

    if is_bot_event:
        return {
            'statusCode': 200,
            'body': json.dumps({ 'message': 'Bot triggered this event' })
        }

    return None


def handle_message(slack_event, persona):
    """
    A function to handle a message event from Slack. This will send the
    message to the SQS queue for processing since we cannot guarantee
    that the Lambda function will be able to process the message in
    the 3 second timeout that Slack expects.
    For more information on message events, see:
    https://api.slack.com/events/message

    Args:
        slack_event (dict): The event dictionary from the Slack event
        persona (str): The name of the persona to use for the message
        
    Returns:
        dict: A 200 response indicating that the message was processed successfully.
    """

    # Extract the channel ID and text from the Slack event
    channel_id = slack_event.get("event").get("channel")
    text = slack_event.get("event").get("text")

    # Send the channel ID, text, and persona to the SQS queue
    sqs_queue = sqs_client.Queue(SQS_QUEUE_URL)
    sqs_queue.send_message(
        MessageBody=json.dumps({
            'channel_id': channel_id,
            'text': text,
            'persona': persona
        })
    )

    return {
        'statusCode': 200,
        'body': json.dumps({ 'message': 'Message processed successfully' })
    }


def handler(event, context):
    """
    The AWS Lambda handler function. This function is called by AWS Lambda
    when an event is sent to the Lambda function.

    Args:
        event (dict): The event that triggered the Lambda function
        context (dict): The context in which the Lambda function was called

    Returns:
        dict: A 200 response indicating that the event was handled successfully.

    Raises:
        Exception: Any exception raised by the function will be raised to the caller.
    """
    try:

        # Extracting persona and body from the event
        persona = event.get("pathParameters").get("persona")
        request_body = event.get("body")

        # Parsing the request body into a JSON object
        slack_event = json.loads(request_body)

        # Printing the Slack event to the logs
        # so we can verify what the event looks like for debugging.
        print(f"Slack event: {slack_event}")

        # Handling Slack challenge
        handle_challenge_response = handle_challenge(slack_event)
        if handle_challenge_response is not None:
            return handle_challenge_response

        # Handling Slack bot events
        handle_bot_response = handle_bot(slack_event)
        if handle_bot_response is not None:
            return handle_bot_response


        # Handling Slack messages
        message_response = handle_message(slack_event, persona)
        return message_response

    except Exception as e:
        print(e)
        return {
            'statusCode': 500,
            'body': json.dumps({ 'message': 'Error processing message' })
        }