
s3baseURL="https://s3.us-east-2.amazonaws.com/shareentreprise/"

def getS3url(id) :
    return s3baseURL + id + ".jpg"
