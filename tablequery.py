# -*- coding: utf-8 -*-

from __future__ import print_function # Python 2/3 compatibility
import boto3
import json
import decimal
from boto3.dynamodb.conditions import Key, Attr

# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)



dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
table = dynamodb.Table('catalogue')


def queryOnTable(section, word):

    if not section == None:
        response = table.query(
            KeyConditionExpression=Key('section').eq(section),
            FilterExpression =Attr('nom').contains(word)
        )
    else:
        response = table.scan(
            FilterExpression =Attr('nom').contains(word)
        )

    for i in response['Items']:
        # convert(i)
        print(i['section'].encode("utf-8", "ignore"))
        print(i['nom'].encode("utf-8", "ignore"))

    return response

def getSection(input):
    return {
        "culture": "culture&multimédia",
        "jardin":"jardinage",
        "loisirs": "loisirs",
        "brico":"bricolage",
        "bébé": "bébé",
        "cuisine":"cuisine",
        "tech":"high tech",
        "autre": "autre",
        "catalogue": None,
    }.get(input, "help")  # 10 is default if input not found



