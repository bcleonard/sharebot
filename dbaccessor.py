from __future__ import print_function # Python 2/3 compatibility
import boto3
import botocore
import json

from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)

        #dynamodb = boto3.resource("dynamodb", region_name='us-west-2', endpoint_url="http://localhost:8000")
dynamodb = boto3.resource('dynamodb',region_name='us-east-2')



table = dynamodb.Table('shareEntreprise_Catalogue')

id = "10001"

s3 = boto3.resource('s3')
#for bucket in s3.buckets.all():
#    print(bucket.name)

try:
    s3.Bucket('shareentreprise').download_file('10001.jpg', './pics/10001.jpg')
except botocore.exceptions.ClientError as e:
    if e.response['Error']['Code'] == "404":
        print("The object does not exist.")
    else:
        raise


try:
    response = table.get_item(
        Key={
            'id': id
        }
    )
except ClientError as e:
    print(e.response['Error']['Message'])
else:
    item = response['Item']
    print("GetItem succeeded:")
    print(json.dumps(item, indent=4, cls=DecimalEncoder))