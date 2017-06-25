
from __future__ import print_function # Python 2/3 compatibility
import boto3
import json
import decimal

dynamodb = boto3.resource('dynamodb', region_name='us-east-2')

table = dynamodb.Table('catalogue')

with open("objets_22_06_17_v2.json") as json_file:
    catalogue = json.load(json_file,encoding='utf-8')
    for item in catalogue:
        description = None
        complement = None
        
        section = item['section']
        id = item['id']
        nom = item['nom']
        ownerMail = item['ownerMail']
        if "complement" in item :
            complement = item['complement']

        i={
           'section': section,
           'nom': nom,
           'id': id,
           'ownerMail': ownerMail,
        }

        if not complement is None:
            i['complement'] = complement

        print("Adding item:", id)
            
        response = table.put_item(Item=i)
        print(response['ResponseMetadata']['RetryAttempts'])
        print(response['ResponseMetadata']['HTTPStatusCode'])