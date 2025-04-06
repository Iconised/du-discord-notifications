import xml.etree.ElementTree as ET
import requests, json, os, traceback, re
from datetime import datetime as dt
from datetime import timedelta as td
try:
    constructs = json.load(open('data.json','r'))
except:
    constructs = {}

######################## Enter Discord auth token here ###########################
DISCORD_TOKEN = "ADD TOKEN HERE"
##################################################################################

########## Enter discord channel ID here #############
channelID = "ADD CHANNEL ID HERE"
######################################################

########### Radar Station Location #############
location = "Jago Mission Pickup"
################################################

def getLatestFile():
    log_dir = os.path.join(os.environ['localappdata'],'NQ','DualUniverse','log') + '/'

    log_files = []
    latest_log = ''
    last_mod = 0
    for file in os.listdir(log_dir):
        if file.endswith('.xml'):
            log_files.append(file)
            mTime = os.stat(log_dir + file).st_mtime
            if mTime > last_mod:
                latest_log = file
                last_mod = mTime
    return latest_log

def follow(file, sleep_sec=0.1):
    """ Yield each line from a file as they are written.
    `sleep_sec` is the time to sleep after empty reads. """
    line = ''
    record = False
    recordLines = ''
    while True:
        tmp = file.readline()
        if tmp is not None:
            line += tmp
            if line.endswith("\n"):
                if '<record>' in line:
                    record = True
                    recordLines += line.replace('[Server -> Client] ','').replace('<lambda_2>','')
                elif '</record>' in line:
                    record = False
                    recordLines += line
                    try:
                        XML = ET.ElementTree(ET.fromstring(recordLines))
                        root = XML.getroot()
                    except Exception as e:
                        root = []
                    recordLines = ''
                    for child in root:
                        if child.tag == 'millis':
                            date = dt.fromtimestamp(int(child.text)/1000)
                        if child.tag == 'message':
                            message = child.text
                    if root and message and 'Construct appeared' in message and 'kind = Radar' in message:
                        yield (date,message,'entered radar')
                    elif root and message and '[Server -> Client] Construct disappeared' in message and 'kind = Radar' in message:
                        yield (date,message,'left radar')
                elif record and '<method>' not in line and '<class' not in line and '<resources' not in line and 'storing cache entry' not in line:
                    recordLines += line
                line = ''
                
        elif sleep_sec:
            time.sleep(sleep_sec)

def discordPost(text,channelID=None,Token=None):

    DISCORD_URL = 'https://discordapp.com/api/channels/{}/messages'.format(channelID)
    DISCORD_HEADERS = { "Authorization":"Bot {}".format(Token),
            "User-Agent":"myBotThing (http://some.url, v0.1)",
            "Content-Type":"application/json", }
    try:
        discordContent = '<t:{0:.0f}:R> {1}'.format(dt.now().timestamp(),text)
        postData = json.dumps({'content':discordContent})
        r = requests.post(DISCORD_URL,headers = DISCORD_HEADERS, data = postData)
    except Exception as e:
        print(e)

if __name__ == '__main__':
    log_dir = os.path.join(os.environ['localappdata'],'NQ','DualUniverse','log') + '/'
    latest_log = getLatestFile()
    
    lastLog = dt.now()
    with open(log_dir + latest_log, 'r') as file:
        for line in follow(file):
            try:
                if (dt.now() - line[0]).seconds < 30:
                    construct = re.search(r'constructId\s*?=\s*?(\d+)',line[1]).group(1)
                    if construct in constructs:
                        name = constructs[construct]['name']
                        size = constructs[construct]['size']
                        cType = constructs[construct]['type']
                    else:
                        name = 'Unknown'
                        size = 'Unknown'
                        cType = 'Unknown'
                    text = '(%s) Name: %s | Size - %s | %s at %s'%(construct,name,size,line[2],location)
                    print('{0} - {1}'.format(str(line[0]),text))
                    if cType.lower() != 'static':
                        discordPost(text,channelID,DISCORD_TOKEN)
            except Exception as e:
                traceback.print_exc()
        file.close()


