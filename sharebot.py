# -*- coding: utf-8 -*-

from flask import Flask, request, abort
# import the requests library so we can use it to make REST calls
import requests
import json
import time
import datetime
import urllib2
import tablequery

from tablequery import *
from s3accessor import getS3url

#from democonfig import *

spark_headers = {}
spark_headers["Content-type"] = "application/json; charset=utf-8"

# disable warnings about using certificate verification
requests.packages.urllib3.disable_warnings()

app = Flask(__name__)


def getmessage(message_id):
    # login to developer.ciscospark.com and copy your access token here
    # Never hard-code access token in production environment
    print ("ade: getmessage with id:"+message_id)
    # create request url using message ID
    get_rooms_url = "https://api.ciscospark.com/v1/messages/" + message_id
    # send the GET request and do not verify SSL certificate for simplicity of this example

    api_response = requests.get(get_rooms_url, headers=spark_headers)

    #print api_response.json()
    # parse the response in json
    response_json = api_response.json()
    # get the text value from the response
    if api_response.status_code == 200 :
        text = response_json["text"]
        print("From Spark, message is:"+text)
        # return the text value
        return text
    else :
        return ""

##-------------------------------------------
# webhook from spark
def setup_webhook(target, webhook_name = "webhook"):
    spark_u = "https://api.ciscospark.com/v1/webhooks"

    first = requests.get(spark_u, headers = spark_headers)
    webhooks = first.json()["items"]

    pprint(webhooks)

    # Look for a Web Hook for the Room
    webhook_id = ""
    for webhook in webhooks:
        # If Web Hook already created, don't create again
        print("ade: found a webhook :" +webhook["name"] + " and :" +webhook_name)
        if webhook_name == webhook["name"]:
            str = spark_u + '/' + webhook["id"]
            print("ade: about to remove id:"+str)
            requests.delete(str, headers=spark_headers)
            print ("ade: found webhook already, remove it! ")

    print ("ade: create fresh webhook! ")
    spark_body = {
        "name" : webhook_name,
        "targetUrl" : target,
        "resource" : "messages",
        "event" : "created",
        "secret": spark_token
    }
    page = requests.post(spark_u, headers = spark_headers, json=spark_body)
    webhook = page.json()
    return webhook


def structureResp(item):
    s = item['nom']
    if "complement" in item:
        s += item['complement']
    s+= item['id']
    file = getS3url(item['id'])

    ret = {
        'response': s,
        'photo': file
    }

    return ret

def sayThankYou():
    s = "# :( mauvaise nouvelle ... Sharebot n'a pas trouvé  !! \n"
    s+= " Sharebot veut être gentil et serviable, mais mon patron a du me câbler à l'envers :)\n"
    s+= " Pensez à moi si vous trouvez cet objet, je serai gentil et serviable pour les autres, promis !\n"
    return s

##-------------------------------------------
# webhook from spark
@app.route('/', methods =['POST'])
def inputFromSpark():
    print("ade: input from spark !!")
    # Get the json data
    json = request.json
    print(json)
    # parse the message id, person id, person email, and room id
    # ToDo: force constraints for json parsing - not required for demo
    message_id = json["data"]["id"]
    person_id = json["data"]["personId"]
    person_email = json["data"]["personEmail"]
    room_id = json["data"]["roomId"]

    print("ade: message id:" +message_id)

    # First make sure not processing a message from the bot
    if person_email == bot_email:
        print("ade: return as message is from self !")
        return ''

    # convert the message id into readable text
    message = getmessage(message_id)
    print("From Spark (in main loop), message is:" + message)
    arr = message.split(' ')

    if len(arr) >= 1 :
        section_nickname=arr[0]
    if len(arr) >= 2:
        value=arr[1]

    section = getSection(section_nickname)

    if section != "help" and len(value) >= 1:
           i = 0
           print("ade: call to table !")
           resp = queryOnTable(section,value.lower())
           for i in resp['Items']:
               print(i['section'].encode("utf-8", "ignore"))
               print(i['nom'].encode("utf-8", "ignore"))
               ret = structureResp(i)
               print("ade: response:"+ret['response'])
               print("ade: file constructed:"+ret['photo'])
               toSpark(ret['response'],room_id,ret['photo'])

           if i == 0:
               toSpark(sayThankYou(),room_id,None)

    else:
        toSpark(getHelpMenu("Sharebot n'a pas compris ce message :" +message+"\n"), room_id, None)

    return 'Ok'

##-------------------------------------------
# send back string that contains help menu
def getHelpMenu(sometext):

    if len(sometext) != 0 :
        helpString = sometext
    else:
        helpString = ""

    helpString +="## -- Menu d'aide --\n"
    helpString += "Voici quelques commandes que je connais :\n"
    helpString += " - catalogue BD (pour chercher dans tout le catalogue !)\n"
    helpString += " - culture livre (pour chercher dans la **section culture** les objets 'livre')\n"
    helpString += " - brico perceuse (pour chercher dans la **section brico** les objets 'perceuse')\n"
    helpString += "\n"
    helpString += "voici les sections que je connais: [culture,jardin,loisirs,brico,bebe,cuisine,tech,autre]\n"
    return helpString.encode("utf-8", "ignore")


##-------------------------------------------
# POST Function  that sends sometext in markdown to a Spark room
def toSpark(sometext, room_id, file):
    print("ade: toSpark!")
    url = 'https://api.ciscospark.com/v1/messages'
    values = {
        'roomId': room_id,
        'markdown': sometext,
    }

    if not file is None:
        values['files'] = file

    data = json.dumps(values)
    print ("ade: before sending back to spark, print data: "+data)
    req = urllib2.Request(url = url , data = data , headers = spark_headers)
    response = urllib2.urlopen(req)
    the_page = response.read()
    return the_page


##-------------------------------------------
# main()
if __name__ == '__main__':

    from argparse import ArgumentParser
    import os, sys
    from pprint import pprint

    # Setup and parse command line arguments
    parser = ArgumentParser("sharentreprise Spark Interaction Bot")
    parser.add_argument(
        "-t", "--token", help="Spark User Bearer Token", required=False
    )
    parser.add_argument(
        "-a", "--app", help="Address of app server", required=False
    )
    parser.add_argument(
        "-d", "--dir", help="Address of directory server", required=False
    )
    parser.add_argument(
        "-p", "--photo", help="Address of photo directory server", required=False
    )
    parser.add_argument(
        "-u", "--boturl", help="Local Host Address for this Bot", required=False
    )
    parser.add_argument(
        "-b", "--botemail", help="Email address of the Bot", required=False
    )
    parser.add_argument(
        "-f", "--dispo", help="Address of dispo server", required=False
    )
    parser.add_argument(
        "--demoemail", help="Email Address to Add to Demo Room", required=False
    )
    parser.add_argument(
        "--logroomid", help="Cisco Spark Room ID to log messages", required=False
    )
    parser.add_argument(
        "--localport", help="Cisco Spark local port for ngrok redirection", required=True
    )

    # parser.add_argument(
    #     "-s", "--secret", help="Key Expected in API Calls", required=False
    # )
    args = parser.parse_args()

    # Set application run-time variables
    bot_url = args.boturl
    if (bot_url == None):
        bot_url = os.getenv("roomfinder_spark_bot_url")
        if (bot_url == None):
            bot_url = raw_input("What is the URL for this Spark Bot? ")
    # print "Bot URL: " + bot_url
    sys.stderr.write("Bot URL: " + bot_url + "\n")

    bot_email = args.botemail
    if (bot_email == None):
        bot_email = os.getenv("roomfinder_spark_bot_email")
        if (bot_email == None):
            bot_email = raw_input("What is the Email Address for this Bot? ")
    # print "Bot Email: " + bot_email
    sys.stderr.write("Bot Email: " + bot_email + "\n")

    bot_name = bot_email.split('@')[0]
    sys.stderr.write("Bot Name: " + bot_name + "\n")


    spark_token = args.token
    # print "Spark Token: " + str(spark_token)
    if (spark_token == None):
        spark_token = os.getenv("spark_token")
        # print "Env Spark Token: " + str(spark_token)
        if (spark_token == None):
            get_spark_token = raw_input("What is the Cisco Spark Token? ")
            # print "Input Spark Token: " + str(get_spark_token)
            spark_token = get_spark_token
    # print "Spark Token: " + spark_token
    # sys.stderr.write("Spark Token: " + spark_token + "\n")
    sys.stderr.write("Spark Token: REDACTED\n")


    local_port = int(args.localport)

    # Set Authorization Details for external requests
    spark_headers["Authorization"] = "Bearer " + spark_token

    # Setup Web Hook to process demo room messages
    webhook_id = setup_webhook(bot_url, "webhook")
    #sys.stderr.write("sharebot Web Hook ID: " + webhook_id + "\n")


    app.run(host='0.0.0.0' , port=local_port)
