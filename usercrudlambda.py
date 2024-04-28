import json
import boto3
from decimal import Decimal
import hashlib
import uuid

client = boto3.client('dynamodb')
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table('Users')  # Assuming this is your UserTable
tableName = 'http-crud-tutorial-items'  # Not used, can be removed


def hash_password(password):
    # Function to hash the password before storing
    return hashlib.sha256(password.encode()).hexdigest()


def lambda_handler(event, context):
    print(event)
    body = {}
    statusCode = 200
    headers = {
        "Content-Type": "application/json"
    }

    try:
        if event['routeKey'] == "DELETE /users/{UserId}":
            table.delete_item(
                Key={'UserId': event['pathParameters']['UserId']})
            body = 'Deleted user ' + event['pathParameters']['UserId']
        elif event['routeKey'] == "GET /users/{UserId}":
            response = table.get_item(
                Key={'UserId': event['pathParameters']['UserId']})
            if 'Item' in response:
                user_data = response['Item']
                # Masking the password before returning
                user_data['Password'] = "********"
                body = user_data
            else:
                statusCode = 404
                body = "User not found"
        elif event['routeKey'] == "GET /users":
            response = table.scan()
            users = response.get('users', [])
            # Masking passwords before returning
            for user in users:
                user['Password'] = "********"
            body = users
        elif event['routeKey'] == "POST /users":
            requestJSON = json.loads(event['body'])
            hashed_password = hash_password(requestJSON['Password'])
            table.put_item(
                Item={
                    'UserId': str(uuid.uuid4()),
                    'Name': requestJSON['Name'],
                    'ContactNumber': requestJSON['ContactNumber'],
                    'Address': requestJSON['Address'],
                    'City': requestJSON['City'],
                    'Password': hashed_password
                })
            body = 'User data Created '
        else:
            statusCode = 400
            body = 'Unsupported route: ' + event['routeKey']
    except KeyError:
        statusCode = 400
        body = 'Unsupported route: ' + event['routeKey']

    body = json.dumps(body)
    res = {
        "statusCode": statusCode,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": body
    }
    return res
