import boto3
import json
import logging
import requests

from botocore.exceptions import ClientError
from os import environ


def lambda_handler(event, context):
    """Asyncronous function to add AWS IP address ranges to DynamoDB table

    Event contains SNS message from IP address ranges described here:
    https://docs.aws.amazon.com/vpc/latest/userguide/aws-ip-ranges.html#subscribe-notifications

    """

    if environ.get("DYNAMODB_TABLE") is not None:
        ENV_TABLE = environ.get("DYNAMODB_TABLE")
        REGION = environ.get("REGION")
    else:
        print("ERROR: Environment Variable DYNAMODB_TABLE not set, exiting...")
        exit(1)

    # Documentation for ip-ranges.json here:
    # https://docs.aws.amazon.com/vpc/latest/userguide/aws-ip-ranges.html#aws-ip-syntax

    # Synctoken is the publication time of the ip-ranges.json file in Unix epoch time format.
    synctoken = None

    # Download ipranges json file (do not write to file)
    # ipranges_json_url = "https://ip-ranges.amazonaws.com/ip-ranges.json"

    print(
        f'DEBUG: event["Records"][0]["Sns"]["Message"]: {event["Records"][0]["Sns"]["Message"]}'
    )

    message_json = json.loads(event["Records"][0]["Sns"]["Message"])

    print(f"DEBUG: message_json: {message_json}")

    ipranges_json_url = message_json["url"]

    print(f"DEBUG: ipranges_json_url: {ipranges_json_url}")

    if "https" not in ipranges_json_url:
        print(f"DEBUG: Setting url manually....")
        ipranges_json_url = "https://ip-ranges.amazonaws.com/ip-ranges.json"

    try:
        print(f"DEBUG: Downloading json from {ipranges_json_url}...")
        r = requests.get(ipranges_json_url)
    except requests.exceptions.ConnectionError as e:
        logging.error("Error: Received requests.exceptions.ConnectionError, Exiting...")
        exit(1)
    except Exception as e:
        logging.error("Error: Received exception {},  Exiting...".format(type(e)))
        exit(1)

    if r.status_code != 200:
        logging.error("Error: requests.get failed, Exiting...")
        exit(1)
    else:
        print(f"DEBUG: download successful.")

    try:
        ipranges_json = r.json()
    except requests.exceptions.JSONDecodeError:
        logging.error("Error: Received JSONDecodeError, Exiting...")
        exit(1)
    except Exception as e:
        logging.error("Error: Received exception {},  Exiting...".format(type(e)))
        exit(1)

    synctoken = ipranges_json["syncToken"]

    print(f"synctoken: {synctoken}")

    # Create DDB resource client

    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb/table/put_item.html
    ddb = boto3.resource("dynamodb", region_name=REGION)
    table = ddb.Table(ENV_TABLE)

    # Add synctoken to allow removing old versions later
    PK = "SYNCTOKEN#"
    SK = synctoken
    try:
        response = table.put_item(
            Item={
                "PK": PK,
                "SK": SK,
                "synctoken": synctoken,
            }
        )
    except ClientError as err:
        logging.error(
            'Error: Couldn\'t add item to DynamoDB table: "%s". Error Code: %s: Error Message: %s',
            "ipranges",
            err.response["Error"]["Code"],
            err.response["Error"]["Message"],
        )
        raise

    print("DEBUG: Added synctoken to db")

    count1 = 0
    count2 = 0
    for i in ipranges_json["prefixes"]:
        if "ip_prefix" in i:
            if count1 == 0:
                print(f"DEBUG: item 1: {i}")
            # construct item to be added to ddb
            # PK looks like: PREFIX#us-west-2#EC2
            PK = "PREFIX#" + i["region"] + "#" + i["service"]
            SK = "#IPV4#" + i["ip_prefix"]
            try:
                response = table.put_item(
                    Item={
                        "PK": PK,
                        "SK": SK,
                        "prefix": i["ip_prefix"],
                        "region": i["region"],
                        "service": i["service"],
                        "network_border_group": i["network_border_group"],
                        "synctoken": synctoken,
                    }
                )
                count1 += 1
            except ClientError as err:
                logging.error(
                    'Error: Couldn\'t add item to DynamoDB table: "%s". Error Code: %s: Error Message: %s',
                    "ipranges",
                    err.response["Error"]["Code"],
                    err.response["Error"]["Message"],
                )
                raise
    print(
        f"DEBUG: Successful put_item() executed for {count1} ipv4 prefixes entries..."
    )

    for i in ipranges_json["ipv6_prefixes"]:
        if "ipv6_prefix" in i:
            # construct item to be added to ddb
            # PK looks like: PREFIX#us-west-2#EC2
            PK = "PREFIX#" + i["region"] + "#" + i["service"]
            SK = "#IPV6#" + i["ipv6_prefix"]
            try:
                response = table.put_item(
                    Item={
                        "PK": PK,
                        "SK": SK,
                        "prefix": i["ipv6_prefix"],
                        "region": i["region"],
                        "service": i["service"],
                        "network_border_group": i["network_border_group"],
                        "synctoken": synctoken,
                    }
                )
                count2 += 1
            except ClientError as err:
                logging.error(
                    'Error: Couldn\'t add item to DynamoDB table: "%s". Error Code: %s: Error Message: %s',
                    "ipranges",
                    err.response["Error"]["Code"],
                    err.response["Error"]["Message"],
                )
                raise
    print(
        f"DEBUG: Successful put_item() executed for {count2} ipv6 prefixes entries..."
    )
