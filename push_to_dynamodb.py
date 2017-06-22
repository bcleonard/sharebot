
from __future__ import print_function # Python 2/3 compatibility
import boto3
import json
import decimal

dynamodb = boto3.resource('dynamodb', region_name='us-east-2')

table = dynamodb.Table('shareEntreprise_catalogue')

with open("objets_22_06_17.json") as json_file:
    catalogue = json.load(json_file,encoding='latin1')
    for item in catalogue:
        description = None
        complement = None
        
        id = item['id']
        name = item['name']
        section = item['section']
        if "description" in item :
            description = item['description']
        if "complement" in item :
            complement = item['complement']
        ownerMail = item['ownerMail']

        i={
           'id': id,
           'name': name,
           'section': section,
           'ownerMail': ownerMail,
        }
        if not description is None:
            i['description']  = description
        if not complement is None:
            i['complement']  = complement

        print("Adding item:", id)
            
        table.put_item(Item=i)