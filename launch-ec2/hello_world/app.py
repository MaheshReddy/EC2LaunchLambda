import json
import botocore.session
import time
import requests #dependency
import json

# TODO write fking tests

def post_to_discord(message):
    """
    Thanks to Bilka2@ copied from
    https://gist.github.com/Bilka2/5dd2ca2b6e9f3573e0c2defe5d3031b2
    """
    url =
    "https://discord.com/api/webhooks/734283497484713985/1HgmuHDxzhtViwsVk5i0IOSbl5vNiFQNIxzjMSlWl3aeaviSlgvTjeUkvB0FCF38lpgT"
    
    data = {}
    #for all params, see https://discordapp.com/developers/docs/resources/webhook#execute-webhook
    data["content"] = message 
    data["username"] = "aws_bot"
    
    #leave this out if you dont want an embed
    data["embeds"] = []
    #embed = {}
    ##for all params, see https://discordapp.com/developers/docs/resources/channel#embed-object
    #embed["description"] = "text in embed"
    #embed["title"] = "embed title"
    #data["embeds"].append(embed)
    
    result = requests.post(url, data=json.dumps(data), headers={"Content-Type": "application/json"})
    
    try:
        result.raise_for_status()
    except requests.exceptions.HTTPError as err:
        return "Error posting to discord {}".format(err)
    else:
        return "Payload delivered successfully, code {}.".format(result.status_code)

def start_server(event, context):
    session = botocore.session.get_session()
    client = session.create_client('ec2', region_name='us-west-2')
    #TODO add checks about current state of instance
    client.start_instances(InstanceIds=['i-068a66b7bc6c1e0f2'])
    server = None

    while True:
        count = 0
        server = client.describe_instances(
            InstanceIds=['i-068a66b7bc6c1e0f2']
        ).get('Reservations')[0].get('Instances')[0]
        if server.get('PublicIpAddress') or count == 25:
            break
        time.sleep(1)
        count = count + 1

    if server:
        message = "Started instance id: i-068a66b7bc6c1e0f2 ip:{}".format(server.get('PublicIpAddress'))
    else:
        message = "Unable to start instance i-068a66b7bc6c1e0f2"

    discord_out = post_to_discord(message)
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "message:{} discord:{}".format(message,discord_out),
        }),
    }

def stop_server(event, context):
    session = botocore.session.get_session()
    client = session.create_client('ec2', region_name='us-west-2')
    #TODO add checks about current state of instance
    client.stop_instances(InstanceIds=['i-068a66b7bc6c1e0f2'])
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "stoped instance id: i-068a66b7bc6c1e0f2",
        }),
    }

routes = {
    #Start the server
    '/start_server' : start_server,
    #Retrieve Elasticast Config File Endpoint
    '/stop_server' : stop_server,
}

def done(status_code, body, content_type='application/json', is_based_64_encoded = False):
    '''
    Utility for creating a response to API call
    params: status_code: Status code
            body: Body Information
            content_type: Content type, application/json by default
            is_based_64_encoded : Is the content based 64 encoded, false by default
    return: Dictionary of the the response
    '''
    
    return {
        'statusCode': status_code,
        'isBase64Encoded': is_based_64_encoded,
        'body': body,
        'headers': {
          'Content-Type': content_type
        }
    }

def lambda_handler(event, context):
    '''
    Handler for all python functions. Also handles routing.
    params: event: Lambda provided event
            context: Lambda provided context
    return: Response to request.
    '''

    for route in routes:
        if route in event['path']:
            return routes[route](event, context)
    else:
        return done(404, '{"message": "Path Not Found"}', 'application/json')
