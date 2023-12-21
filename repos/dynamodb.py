import boto3
from boto3_type_annotations.dynamodb import ServiceResource

from domain.user import User
from domain.device import Device

dynamodb_client : ServiceResource = boto3.resource(
    'dynamodb',
    region_name='us-east-1',
)

class DynamoRepository:
    def __init__(self, token):
        # Retrieve user by token
        self.__user = token

    def get_user(self):
        return self.__user
    
    def get_user_info(self):
        users = dynamodb_client.Table('users')
        response = users.get_item(
            Key={'userId': self.get_user()}
        )
        item = response.get('Item')
        return User.from_dict(item) if item else User(user_id=self.get_user())
    
    def get_device(self, device_id):
        devices = dynamodb_client.Table('devices')
        response = devices.get_item(
            Key={'deviceId': device_id}
        )
        item = response.get('Item')
        return Device.from_dict(item) if item else None