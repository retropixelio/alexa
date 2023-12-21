from domain.event import Request
from domain.authentication import Token, FirebaseToken
from repos.response import response_object

class TokenAuthentication:
    def authenticate(self, request: Request):
        try:
            token = Token(token=request.headers.authorization[7:])
            user = token.decode()
            return user.user_id
        except:
            return False
        
class FirebaseAuthentication:
    def authenticate(self, request: Request):
        try:
            token = FirebaseToken(token=request.headers.authorization[7:])
            user = token.decode()
            return user.user_id
        except Exception as e:
            print(e)
            return False

class APIView:
    authentication_classes = []

    def __init__(self, request: Request):
        self.request = request
        self.user = None

    def execute(self):
        for auth in self.authentication_classes:
            user = auth().authenticate(self.request)
            if user:
                self.user = user
            else:
                return response_object({}, 401)
        if self.request.http_method == 'OPTIONS':
            return{
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,DELETE'
                }
            }
        if self.request.http_method.lower() in dir(self):
            function = getattr(self, self.request.http_method.lower())
            return function()
        return response_object({}, 405)