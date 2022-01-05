from __future__ import print_function
import json
import os
from urllib import request, parse


def findings_message(json_data):
    
    try:
        findings = json_data["Findings"]

        slack_message = {"fallback": "A new message", "fields": [{"title": "Vulnerable domains"}]}

        for finding in findings:

            print(f"{finding['Domain']} in {finding['Account']} AWS Account")

            slack_message["fields"].append(
                {"value": f"{finding['Domain']} in {finding['Account']} AWS Account", "short": False}
            )

        return slack_message

    except KeyError:

        return None

def takeovers_message(json_data):

    try:
        takeovers = json_data["Takeovers"]

        slack_message = {"fallback": "A new message", "fields": [{"title": "Domains taken over"}]}

        for takeover in takeovers:

            print(
                f"{takeover['TakeoverStatus']}: {takeover['ResourceType']} {takeover['TakeoverDomain']} domain created in {takeover['TakeoverAccount']} AWS account to protect {takeover['TakeoverDomain']} in {takeover['VulnerableAccount']} account"
            )

            if takeover["TakeoverStatus"] == "success":
                slack_message["fields"].append(
                    {
                        "value": f"{takeover['ResourceType']} {takeover['TakeoverDomain']} successfully created in {takeover['TakeoverAccount']} AWS account to protect {takeover['VulnerableDomain']} domain in {takeover['VulnerableAccount']} Account",
                        "short": False,
                    }
                )

            if takeover["TakeoverStatus"] == "failure":
                slack_message["fields"].append(
                    {
                        "value": f"{takeover['ResourceType']} {takeover['TakeoverDomain']} creation failed in {takeover['TakeoverAccount']} AWS account to protect {takeover['VulnerableDomain']} domain in {takeover['VulnerableAccount']} Account",
                        "short": False,
                    }
                )
        
        return slack_message
    
    except KeyError:
        
        return None


def resources_message(json_data):

    try:
        stacks = json_data["Resources"]

        slack_message = {"fallback": "A new message", "fields": [{"title": "Resources preventing hostile takeover"}]}

        for tags in stacks:

            for tag in tags:

                if tag["Key"] == "ResourceName":
                    resource_name = tag["Value"]

                elif tag["Key"] == "ResourceType":
                    resource_type = tag["Value"]

                elif tag["Key"] == "TakeoverAccount":
                    takeover_account = tag["Value"]

                elif tag["Key"] == "VulnerableAccount":
                    vulnerable_account = tag["Value"]

                elif tag["Key"] == "VulnerableDomain":
                    vulnerable_domain = tag["Value"]

            print(
                f"{resource_type} {resource_name} in {takeover_account} AWS account protecting {vulnerable_domain} domain in {vulnerable_account} Account"
            )

            slack_message["fields"].append(
                {
                    "value": f"{resource_type} {resource_name} protecting {vulnerable_domain} domain in {vulnerable_account} Account",
                    "short": False,
                }
            )

        slack_message["fields"].append(
            {
                "value": "After fixing DNS issues, delete resources and CloudFormation stacks",
                "short": False,
            }
        )

        return slack_message

    except KeyError:
        
        return None

def lambda_handler(event, context):  # pylint:disable=unused-argument

    slack_url = os.environ["SLACK_WEBHOOK_URL"]
    slack_channel = os.environ["SLACK_CHANNEL"]
    slack_username = os.environ["SLACK_USERNAME"]
    slack_emoji = os.environ["SLACK_EMOJI"]

    subject = event["Records"][0]["Sns"]["Subject"]

    payload = {
        "channel": slack_channel,
        "username": slack_username,
        "icon_emoji": slack_emoji,
        "attachments": [],
        "text": subject,
    }

    message = event["Records"][0]["Sns"]["Message"]
    json_data = json.loads(message)

    if findings_message(json_data) is not None:
        slack_message = findings_message(json_data)

    elif takeovers_message(json_data) is not None:
        slack_message = takeovers_message(json_data)

    elif resources_message(json_data) is not None:
        slack_message = resources_message(json_data)

    payload["attachments"].append(slack_message)

    data = parse.urlencode({"payload": json.dumps(payload)}).encode("utf-8")
    req = request.Request(slack_url)

    with request.urlopen(req, data):
        print(f"Message sent to {slack_channel} Slack channel")
