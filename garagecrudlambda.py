import json 
import boto3 
import hashlib
from decimal import Decimal
import uuid

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return str(o)
        return super().default(o)

dynamodb = boto3.resource('dynamodb') 
table = dynamodb.Table('MechanicTable') 

def hash_password(password):
    # Encode the password string to bytes
    password_bytes = password.encode('utf-8')
    # Create a SHA-256 hash object
    sha256_hash = hashlib.sha256()
    # Update the hash object with the password bytes
    sha256_hash.update(password_bytes)
    # Get the hexadecimal representation of the hashed password
    hashed_password = sha256_hash.hexdigest()
    return hashed_password
    
def calculate_geohash(latitude, longitude, precision):
    # Define the base32 characters used for encoding
    BASE32 = "0123456789bcdefghjkmnpqrstuvwxyz"
    # Define the intervals for latitude and longitude
    lat_interval = (-90.0, 90.0)
    lon_interval = (-180.0, 180.0)
    # Initialize the geohash string
    geohash = ""
    # Iterate through each bit of precision
    for i in range(precision):
        # Initialize the bit value
        bit = 0
        # Calculate the midpoints for latitude and longitude intervals
        mid_lat = (lat_interval[0] + lat_interval[1]) / 2
        mid_lon = (lon_interval[0] + lon_interval[1]) / 2
        # Update the bit value based on the latitude and longitude
        if latitude >= mid_lat:
            bit |= 1
            lat_interval = (mid_lat, lat_interval[1])
        else:
            lat_interval = (lat_interval[0], mid_lat)
        
        if longitude >= mid_lon:
            bit |= 2
            lon_interval = (mid_lon, lon_interval[1])
        else:
            lon_interval = (lon_interval[0], mid_lon)
        # Append the character corresponding to the bit value to the geohash
        geohash += BASE32[bit]
    return geohash

def lambda_handler(event, context): 
    if event['routeKey'] == 'POST /mechanics':
        data = json.loads(event['body']) 
        mechanic_id = str(uuid.uuid4())
        name = data['Name']
        contact_number = data['ContactNumber']
        password = hash_password(data['Password'])
        address = data['Address']
        city = data['City']
        state = data['State']
        government_id = data['GovernmentId']
        latitude = Decimal(str(data['Latitude']))  # Convert to Decimal
        longitude = Decimal(str(data['Longitude']))  # Convert to Decimal
        location_geohash = calculate_geohash(latitude, longitude, precision=12)
        

        item = {
            'MechanicId': mechanic_id,
            'Name': name,
            'ContactNumber': contact_number,
            'Password': password,
            'Address': address,
            'City': city,
            'State': state,
            'GovernmentId': government_id,
            'Latitude': latitude,
            'Longitude': longitude,
            'LocationGeohash': location_geohash
        }

        table.put_item(Item=item)

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Successfully Registered'})
        }
    
    elif event['routeKey'] == 'DELETE /mechanics/{id}':
        # Check if a specific mechanic ID is provided in the URL path
        if 'id' in event['pathParameters']:
            # Retrieve mechanic ID from path parameters
            mechanic_id = event['pathParameters']['id']
            
            # Delete the item from DynamoDB for the specific mechanic ID
            response = table.delete_item(Key={'MechanicId': mechanic_id})
            
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'Mechanic details deleted successfully'})
            }
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({'message': 'Mechanic ID not provided'})
            }
            
    elif event['routeKey'] == 'GET /mechanics':
    # Retrieve all mechanics' data from DynamoDB
        response = table.scan()
        # Return all mechanics' data
        return {
            'statusCode': 200,
            'body': json.dumps(response['Items'], cls=DecimalEncoder)
        }

    elif event['routeKey'] == 'GET /mechanics/{id}':
        # Check if a specific mechanic ID is provided in the URL path
        if 'id' in event['pathParameters']:
            # Retrieve mechanic ID from path parameters
            mechanic_id = event['pathParameters']['id']
        
            # Retrieve mechanic data from DynamoDB for the specific mechanic ID
            response = table.get_item(Key={'MechanicId': mechanic_id})
        
            # Check if mechanic data exists
            if 'Item' in response:
                # Return mechanic data
                return {
                    'statusCode': 200,
                    'body': json.dumps(response['Item'], cls=DecimalEncoder)
                }
            else:
                #Return error message if mechanic data not found
                return {
                    'statusCode': 404,
                    'body': json.dumps({'message': 'MechanicID Not Found'})
                }
        else:
            # Return error message if mechanic ID is not provided
            return {
                'statusCode': 400,
                'body': json.dumps({'message': 'Mechanic ID not provided'})
            }
    
    else:
        # Return error message if it's not a supported method
        return {
            'statusCode': 400,
            'body': json.dumps({'message': 'Unsupported method'})
        }
