#!/usr/bin/env python
import requests
import json
import yaml

###### User Variables

username = 'admin'
password = 'Arista123'
server1 = 'https://192.168.255.50'
imageName = 'EOS-4.23.4M.swi'
terminAttr = 'TerminAttr-1.9.6-1.swix'
base_container_name = 'Tenant'
containers_To_Build = ['Leaf', 'Spine', 'MGMT-ToR', 'MGMT-Spine']

###### Do not modify anything below this line. Or do, I'm not a cop.
connect_timeout = 10
headers = {"Accept": "application/json",
           "Content-Type": "application/json"}
requests.packages.urllib3.disable_warnings()
session = requests.Session()

def login(url_prefix, username, password):
    authdata = {"userId": username, "password": password}
    headers.pop('APP_SESSION_ID', None)
    response = session.post(url_prefix+'/web/login/authenticate.do', data=json.dumps(authdata),
                            headers=headers, timeout=connect_timeout,
                            verify=False)
    cookies = response.cookies
    headers['APP_SESSION_ID'] = response.json()['sessionId']
    if response.json()['sessionId']:
        return response.json()['sessionId']

def logout(url_prefix):
    response = session.post(url_prefix+'/web/login/logout.do')
    return response.json()

def save_topology(url_prefix):
    response = session.post(url_prefix+'/cvpservice/provisioning/v2/saveTopology.do', data=json.dumps([]))
    return response.json()

def add_configlet(url_prefix,configlet_name,configlet_body):
  tempData = json.dumps({
          "config": configlet_body,
          "name": configlet_name
  })
  response = session.post(url_prefix+'/cvpservice/configlet/addConfiglet.do', data=tempData)
  #return tempData
  return response.json()

def upload_image(url_prefix,imageName):
    with open(imageName, "rb") as imageBinary:
        imageDict = {'file': imageBinary}
        response = session.post(url_prefix+'/cvpservice/image/addImage.do', files=imageDict)
    return response.json()

def add_Bundle(url_prefix,imageBundleName):
    data = {"images": [bundleinfo, terminAttrinfo], "isCertifiedImage": 'true', "name": 'DefaultBundle'}
    response = session.post(url_prefix+'/cvpservice/image/saveImageBundle.do', data=json.dumps(data))
    return response.json()

def add_Container(url_prefix, container_name):
    data = {'data': [{'info': 'adding Container '+container_name,
                          'infoPreview': container_name,
                          'action': 'add',
                          'nodeType': 'container',
                          'nodeId': 'new_container',
                          'toId': 'root',
                          'fromId': '',
                          'nodeName': container_name,
                          'fromName': '',
                          'toName': 'Tenant',
                          'toIdType': 'container'}]}
    response = session.post(url_prefix+'/cvpservice/ztp/addTempAction.do?format=topology&queryParam=&nodeId=root', data=json.dumps(data))
    print json.dumps(data)
    return response.json()

def add_temp_action(url_prefix,container_name,container_key,current_static_key,
          current_static_name,current_builder_key,current_builder_name):
  tempData = json.dumps({
    "data":[
      {
         "info":"Configlet Assign: to container "+container_name,
         "infoPreview":"<b>Configlet Assign:</b> to container "+container_name,
         "action":"associate",
         "nodeType":"configlet",
         "nodeId":"",
         "toId":container_key,
         "fromId":"",
         "nodeName":"",
         "fromName":"",
         "toName":container_name,
         "toIdType":"container",
         "configletList":current_static_key,
         "configletNamesList":current_static_name,
         "ignoreConfigletList":[],
         "ignoreConfigletNamesList":[],
         "configletBuilderList":current_builder_key,
         "configletBuilderNamesList":current_builder_name,
         "ignoreConfigletBuilderList":[],
         "ignoreConfigletBuilderNamesList":[]
      }
   ]
})

  response = session.post(url_prefix+'/cvpservice/ztp/addTempAction.do?format=topology&queryParam=&nodeId=root', data=tempData)
  #return tempData
  return response.json()

print '###### Logging into Server 1'
login(server1, username, password)
print '###### Uploading Image Bundle'
try:
    bundleinfo = upload_image(server1,imageName)
except:
    print 'Failure to upload file. Does it exist already? Is it in the working dir?'
    pass
bundleinfo.pop('result',None)
try:
    terminAttrinfo = upload_image(server1,terminAttr)
except:
    print 'Failure to upload file. Does it exist already? Is it in the working dir?'
    pass
bundleinfo.pop('result',None)
terminAttrinfo.pop('result',None)
try:
    add_Bundle(server1,json.dumps(bundleinfo,terminAttrinfo))
except:
    print 'Add bundle failed for some reason...'
    pass
for container in containers_To_Build:
    try:
        add_Container(server1,container)
    except:
        pass
