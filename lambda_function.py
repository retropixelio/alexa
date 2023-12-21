import json

from repos.response import AlexaResponse
from repos.dynamodb import DynamoRepository
from repos.mqtt import MqttRepo

def lambda_handler(request, context):
    # Dump the request for logging - check the CloudWatch logs.
    print('lambda_handler request  -----')
    print(json.dumps(request))

    if context is not None:
        print('lambda_handler context  -----')
        print(context)

    # Validate the request is an Alexa smart home directive.
    if 'directive' not in request:
        alexa_response = AlexaResponse(
            name='ErrorResponse',
            payload={'type': 'INVALID_DIRECTIVE',
                     'message': 'Missing key: directive, Is the request a valid Alexa Directive?'})
        return send_response(alexa_response.get())

    # Check the payload version.
    payload_version = request['directive']['header']['payloadVersion']
    if payload_version != '3':
        alexa_response = AlexaResponse(
            name='ErrorResponse',
            payload={'type': 'INTERNAL_ERROR',
                     'message': 'This skill only supports Smart Home API version 3'})
        return send_response(alexa_response.get())

    # Crack open the request to see the request.
    name = request['directive']['header']['name']
    namespace = request['directive']['header']['namespace']

    # Handle the incoming request from Alexa based on the namespace.
    if namespace == 'Alexa.Authorization':
        if name == 'AcceptGrant':
            # Note: This example code accepts any grant request.
            # In your implementation, invoke Login With Amazon with the grant code to get access and refresh tokens.
            grant_code = request['directive']['payload']['grant']['code']
            grantee_token = request['directive']['payload']['grantee']['token']
            auth_response = AlexaResponse(namespace='Alexa.Authorization', name='AcceptGrant.Response')
            return send_response(auth_response.get())

    if namespace == 'Alexa':
        if name == 'ReportState':
            token = request['directive']['endpoint']['scope']['token']
            endpoint_id = request['directive']['endpoint']['endpointId']
            correlation_token = request['directive']['header']['correlationToken']
            dynamo_repo = DynamoRepository(token)
            device = dynamo_repo.get_device(endpoint_id)
            onoff = "ON" if device.onoff else "OFF"
            color = device.color.p if device.color else {"hue":0, "saturation":0, "brightness":1}
            online = {"value": "OK"} if device.online else {"value": "UNREACHABLE","reason":"INTERNET_UNREACHABLE"}
            discovery_response = AlexaResponse(namespace='Alexa', name='StateReport', token=token, endpoint_id=endpoint_id, correlation_token=correlation_token)
            discovery_response.add_context_property(namespace='Alexa.EndpointHealth', name='connectivity', value=online)
            discovery_response.add_context_property(namespace='Alexa.PowerController', name='powerState', value=onoff)
            discovery_response.add_context_property(namespace='Alexa.ColorController', name='color', value=color)
            return send_response(discovery_response.get())

    if namespace == 'Alexa.Discovery':
        if name in ['Discover', 'Discover.Response']:
            token = request['directive']['payload']['scope']['token']
            dynamo_repo = DynamoRepository(token)
            user = dynamo_repo.get_user_info()
            # The request to discover the devices the skill controls.
            discovery_response = AlexaResponse(namespace='Alexa.Discovery', name='Discover.Response')
            # Create the response and add the light bulb capabilities.
            capability_alexa = discovery_response.create_payload_endpoint_capability()
            capability_alexa_powercontroller = discovery_response.create_payload_endpoint_capability(
                interface='Alexa.PowerController',
                supported=[{'name': 'powerState'}])
            capability_alexa_colorcontroller = discovery_response.create_payload_endpoint_capability(
                interface='Alexa.ColorController',
                supported=[{'name': 'color'}])
            capability_alexa_endpointhealth = discovery_response.create_payload_endpoint_capability(
                interface='Alexa.EndpointHealth',
                supported=[{'name': 'connectivity'}])
            
            for device in user.devices:
                discovery_response.add_payload_endpoint(
                    friendly_name=device.nickname,
                    endpoint_id=device,
                    capabilities=[capability_alexa, capability_alexa_endpointhealth, capability_alexa_colorcontroller, capability_alexa_powercontroller])
            discovery_response.add_context_property(namespace='Alexa.EndpointHealth', name='connectivity', value='OK')
            discovery_response.add_context_property(namespace='Alexa.PowerController', name='powerState', value='ON')
            discovery_response.add_context_property(namespace='Alexa.ColorController', name='color', value={"hue": 360, "saturation": 1, "brightness": 1})
            return send_response(discovery_response.get())

    if namespace == 'Alexa.ColorController':
        # The directive to TurnOff or TurnOn the light bulb.
        # Note: This example code always returns a success response.
        token = request['directive']['endpoint']['scope']['token']
        endpoint_id = request['directive']['endpoint']['endpointId']
        color_state_value = request['directive']['payload']['color']
        correlation_token = request['directive']['header']['correlationToken']
        color = hsl_to_int(color_state_value)
        # Check for an error when setting the state.
        device_set = update_device_state(endpoint_id=endpoint_id, state='color', value=color, token=token)
        if not device_set:
            return AlexaResponse(
                name='ErrorResponse',
                payload={'type': 'ENDPOINT_UNREACHABLE', 'message': 'Unable to reach endpoint database.'}).get()

        directive_response = AlexaResponse(correlation_token=correlation_token)
        directive_response.add_context_property(namespace='Alexa.ColorController', name='color', value=color_state_value)
        return send_response(directive_response.get())
        
    if namespace == 'Alexa.PowerController':
        # The directive to TurnOff or TurnOn the light bulb.
        # Note: This example code always returns a success response.
        token = request['directive']['endpoint']['scope']['token']
        endpoint_id = request['directive']['endpoint']['endpointId']
        power_state_value = 'OFF' if name == 'TurnOff' else 'ON'
        correlation_token = request['directive']['header']['correlationToken']

        # Check for an error when setting the state.
        device_set = update_device_state(endpoint_id=endpoint_id, state='powerState', value=power_state_value, token=token)
        if not device_set:
            return AlexaResponse(
                name='ErrorResponse',
                payload={'type': 'ENDPOINT_UNREACHABLE', 'message': 'Unable to reach endpoint database.'}).get()

        directive_response = AlexaResponse(correlation_token=correlation_token)
        directive_response.add_context_property(namespace='Alexa.PowerController', name='powerState', value=power_state_value)
        return send_response(directive_response.get())

# Send the response
def send_response(response):
    print('lambda_handler response -----')
    print(json.dumps(response))
    return response

# Make the call to your device cloud for control
def update_device_state(endpoint_id, state, value, token):
    mqtt_repo = MqttRepo()
    if state == 'powerState':
        payload = {
            'deviceId': endpoint_id,
            'onoff': True if value == 'ON' else False
        }
        mqtt_repo.publish(endpoint_id, payload)
        return True
    if state == 'color':
        rgb = (value // 256 // 256 % 256, value // 256 % 256, value % 256)
        payload = {
            'deviceId': endpoint_id,
            'color':{
                'red': rgb[0],
                'green': rgb[1],
                'blue': rgb[2],
                'type': 0
            }
        }
        mqtt_repo.publish(endpoint_id, payload)
        return True

def hsl_to_int(color):
    hue = float(color["hue"]/360)
    saturation = float(color["saturation"])
    brightness = float(color["brightness"])
    rgb = hsv_to_rgb(hue, saturation, brightness)
    hex = '0x'+''.join(["%0.2X" % int(255*c) for c in rgb])
    return int(hex, base=16)

def int_to_hsl(color):
    h = hex(color)[2:].zfill(6)
    rgb = tuple(int(h[i:i+2], 16)/255 for i in (0, 2, 4))
    hsl = rgb_to_hsv(rgb[0],rgb[1],rgb[2])
    return {"hue":360*hsl[0], "saturation":hsl[1], "brightness":hsl[2]}

def hsv_to_rgb(h, s, v):
    if s == 0.0:
        return v, v, v
    i = int(h*6.0) # XXX assume int() truncates!
    f = (h*6.0) - i
    p = v*(1.0 - s)
    q = v*(1.0 - s*f)
    t = v*(1.0 - s*(1.0-f))
    i = i%6
    if i == 0:
        return v, t, p
    if i == 1:
        return q, v, p
    if i == 2:
        return p, v, t
    if i == 3:
        return p, q, v
    if i == 4:
        return t, p, v
    if i == 5:
        return v, p, q

def rgb_to_hsv(r, g, b):
    maxc = max(r, g, b)
    minc = min(r, g, b)
    v = maxc
    if minc == maxc:
        return 0.0, 0.0, v
    s = (maxc-minc) / maxc
    rc = (maxc-r) / (maxc-minc)
    gc = (maxc-g) / (maxc-minc)
    bc = (maxc-b) / (maxc-minc)
    if r == maxc:
        h = bc-gc
    elif g == maxc:
        h = 2.0+rc-bc
    else:
        h = 4.0+gc-rc
    h = (h/6.0) % 1.0
    return h, s, v