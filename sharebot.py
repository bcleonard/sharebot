from flask import Flask, request, abort
# import the requests library so we can use it to make REST calls
import requests
import json
import time
import datetime
import urllib2

#from democonfig import *


spark_headers = {}
spark_headers["Content-type"] = "application/json; charset=utf-8"

# disable warnings about using certificate verification
requests.packages.urllib3.disable_warnings()

app = Flask(__name__)

# Read key value from this server
# curl -X GET -H "X-Device-Secret: 12345" http://localhost:9090/getcmdbykey?key=temp
# curl -X GET -H "X-Device-Secret: 12345" http://localhost:9090/getvaluebykey?key=temp

def getmessage(message_id):
    # login to developer.ciscospark.com and copy your access token here
    # Never hard-code access token in production environment
    print ("ade: getmessage")
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
        # return the text value
        return text
    else :
        return ""

##-------------------------------------------
# webhook from spark
@app.route('/', methods=['GET'])
def inputFromGet():
    print("ade: input from get !!")
    # Get the json data
    json = request.json
    # parse the message id, person id, person email, and room id
    # ToDo: force constraints for json parsing - not required for demo
    return

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

##-------------------------------------------
# webhook from spark
@app.route('/', methods =['POST'])
def inputFromSpark():
    print("ade: input from spark !!")
    # Get the json data
    json = request.json
    # parse the message id, person id, person email, and room id
    # ToDo: force constraints for json parsing - not required for demo
    message_id = json["data"]["id"]
    person_id = json["data"]["personId"]
    person_email = json["data"]["personEmail"]
    room_id = json["data"]["roomId"]

    print("ade: with data!"+person_id +person_email)
    print("ade: bot_email = "+bot_email)

    # First make sure not processing a message from the bot
    if person_email is bot_email:
        return ''

    # convert the message id into readable text
    message = getmessage(message_id)
    arr = message.split(' ')

    if len(arr) >= 1 :
        sparkorder=arr[0]
    if len(arr) >= 2:
        sparkkey=arr[1]

    if sparkorder == "cherche"and len(sparkkey) >= 1:
           toSpark("not found in categories, neither in objects :(", room_id)
    elif sparkorder == "help":
        toSpark(getHelpMenu(""), room_id)
    else:
        toSpark(getHelpMenu("command not found "), room_id)

    return 'Ok'

##-------------------------------------------
# send back string that contains help menu
def getHelpMenu(sometext):

    if len(sometext) != 0 :
        helpString = sometext
    else:
        helpString = ""

    helpString +="-- Help Menu --"
    helpString += "Here is a snippet of the available commands:"
    helpString += "sharebot liste {}"
    return helpString


##-------------------------------------------
# POST Function  that sends sometext in markdown to a Spark room
def toSpark(sometext, room_id):
    print("ade: toSpark!")
    url = 'https://api.ciscospark.com/v1/messages'
    values =   {'roomId': room_id, 'markdown': sometext }
    data = json.dumps(values)
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

    print ("ade: before run")
    app.run(host='0.0.0.0' , port=local_port)
