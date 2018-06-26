import uuid
import json
import datetime
import pytz
import requests
from yellowant import YellowAnt
from yellowant.messageformat import MessageClass, MessageAttachmentsClass, MessageButtonsClass, AttachmentFieldsClass
from django.conf import settings
from .models import YellowUserToken


scopes = ['openid',
          'User.Read',
          'Mail.Read' ,
          'offline_access',
          'Mail.ReadWrite',
          'Mail.Send'
        ]

authority = 'https://login.microsoftonline.com'
authorize_url = '{0}{1}'.format(authority, '/common/oauth2/v2.0/authorize?{0}')
token_url = '{0}{1}'.format(authority, '/common/oauth2/v2.0/token')
graph_endpoint = 'https://graph.microsoft.com/v1.0{0}'

def field_check(obj, object_name):
    print("In field_check")
    if obj[object_name] == None:
        return "None"
    else:
        return obj[object_name]

def get_token_from_refresh_token(refresh_token, redirect_uri):
  # Build the post form for the token request
  print("In get_token_from_refresh_token")
  post_data = {
      'grant_type': 'refresh_token',
      'refresh_token': refresh_token,
      'redirect_uri': settings.OUTLOOK_REDIRECT,
      'scope': ' '.join(str(i) for i in scopes),
      'client_id': settings.OUTLOOK_CLIENT_ID,
      'client_secret': settings.OUTLOOK_CLIENT_SECRET
  }

  r = requests.post(token_url, data=post_data)

  try:
    return r.json()
  except:
    return 'Error retrieving token: {0} - {1}'.format(r.status_code, r.text)

def make_api_call(method, url, token, payload=None, parameters=None):
    # Send these headers with all API calls
    headers = {'User-Agent': 'python_tutorial/1.0',
               'Authorization': 'Bearer {0}'.format(token),
               'Accept': 'application/json',
               'Content-Length': "0"}

    # Use these headers to instrument calls. Makes it easier
    # to correlate requests and responses in case of problems
    # and is a recommended best practice.
    request_id = str(uuid.uuid4())
    instrumentation = {'client-request-id': request_id,
                       'return-client-request-id': 'true'}

    headers.update(instrumentation)

    response = None

    if method.upper() == 'GET':
        response = requests.get(url, headers=headers, params=parameters)
    elif method.upper() == 'DELETE':
        response = requests.delete(url, headers=headers, params=parameters)
    elif method.upper() == 'PATCH':
        headers.update({'Content-Type': 'application/json'})
        response = requests.patch(url, headers=headers, data=json.dumps(payload), params=parameters)
    elif method.upper() == 'POST':
        headers.update({'Content-Type': 'application/json'})
        response = requests.post(url, headers=headers, data=json.dumps(payload), params=parameters)
    return response

class CommandCenter(object):

    def __init__(self, yellowant_user_id, yellowant_integration_id, function_name, args):
        self.yellowant_user_id = yellowant_user_id
        self.yellowant_integration_id = yellowant_integration_id
        self.function_name = function_name
        self.args = args
        self.user_integration = YellowUserToken.objects.get(yellowant_integration_id=self.yellowant_integration_id)
        self.access_token = self.user_integration.outlook_access_token
        self.refresh_token = self.user_integration.outlook_refresh_token
        self.last_update = self.user_integration.token_update
        self.subscription_update = self.user_integration.subscription_update
        self.subscription_id = self.user_integration.subscription_id

    def parse(self):
        self.commands = {
            'user_details': self.user_details,
            'get_my_messages': self.get_my_messages,
            'create_message': self.create_message,
            'list_messages': self.list_messages,
            'mail_folder':self.mail_folder,
            'get_message_byfolder': self.get_message_byfolder,
            'forward_message': self.forward_message,
            'reply': self.reply
        }
        print("In parse")

        print(self.function_name)
        self.user_integration = YellowUserToken.objects.get(yellowant_integration_id=self.yellowant_integration_id)
        self.access_token = self.user_integration.outlook_access_token
        print("123")

        if self.last_update + datetime.timedelta(minutes=57) < pytz.utc.localize(datetime.datetime.utcnow()):
            token = get_token_from_refresh_token(self.refresh_token, settings.OUTLOOK_REDIRECT_URL)
            print("Token is:")
            print(token)
            access_token = token['access_token']
            refresh_token = token['refresh_token']
            YellowUserToken.objects.filter(yellowant_integration_id=self.yellowant_integration_id). \
                update(outlook_access_token=access_token, outlook_refresh_token= \
                refresh_token, token_update=datetime.datetime.utcnow())
            self.refresh_token = refresh_token
            self.access_token = access_token

        if self.subscription_update + datetime.timedelta(minutes=57) < pytz.utc.localize(datetime.datetime.utcnow()):
            graph_endpoint1 = "https://outlook.office.com/api/v2.0{}"
            get_updatewehbhook_url = graph_endpoint1.format('/me/subscriptions/{}'.format(self.subscription_id))

            start_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=4200)
            list = str(start_time).split(" ")
            first_word = list[0] + "T"
            second_word = list[1] + "Z"
            start_time = str(first_word + second_word)
            data = {
                "@odata.type":"#Microsoft.OutlookServices.PushSubscription",
                "SubscriptionExpirationDateTime": start_time
            }
            r = make_api_call('PATCH', get_updatewehbhook_url, self.access_token, payload=data)
            if(r.status_code == 200):
                print("Update json is:")
                print(r.json())
                print(r.status_code)
                current_time = datetime.datetime.utcnow()
                YellowUserToken.objects.filter(outlook_access_token = self.access_token).update(subscription_update = current_time)

        return self.commands[self.function_name](self.args)

    def mail_folder(self, args):
        """gives the relationship between the mail and the folder to which it belongs"""
        print("In mail_folder")
        get_mailFolder_url = graph_endpoint.format('/me/mailFolders')
        r = make_api_call('GET', get_mailFolder_url, self.access_token)
        send_data = {
            'values':[]
        }
        message = MessageClass()
        if (r.status_code == 200):
            obj = r.json()
            data = obj["value"]
            for i in range(0, len(data)):
                obj1 = data[i]
                send_data['values'].append({'displayName': obj1["displayName"], 'id': obj1["id"], 'parentFolderId': str(obj1["parentFolderId"])[0:75]})
            message.data = send_data
            print("returning")
            return message.to_json()
        else:
            print(r.status_code)
            print(r.text)
            return "{0}: {1}".format(r.status_code, r.text)

    def user_details(self, args):
        """It gives the details about the outlook user"""
        print("In user_details")
        get_me_url = graph_endpoint.format('/me')
        print(self.access_token)
        # Use OData query parameters to control the results
        #  - Only return the displayName and mail fields
        r = make_api_call('GET', get_me_url, self.access_token)
        message = MessageClass()
        attachment = MessageAttachmentsClass()
        if (r.status_code == requests.codes.ok):
            print(r.json())
            obj = r.json()

            field1 = AttachmentFieldsClass()
            field1.title = "Display Name"
            field1.value = field_check(obj, "displayName")
            attachment.attach_field(field1)

            field2 = AttachmentFieldsClass()
            field2.title = "Surname"
            field2.value = field_check(obj, "surname")
            attachment.attach_field(field2)

            field3 = AttachmentFieldsClass()
            field3.title = "Given Name"
            field3.value = field_check(obj, "givenName")
            attachment.attach_field(field3)

            field4 = AttachmentFieldsClass()
            field4.title = "Email"
            field4.value = field_check(obj, "userPrincipalName")
            attachment.attach_field(field4)

            field5 = AttachmentFieldsClass()
            field5.title = "Job Title"
            field5.value = field_check(obj, "jobTitle")
            attachment.attach_field(field5)

            field6 = AttachmentFieldsClass()
            field6.title = "Office Location"
            field6.value = field_check(obj, "officeLocation")
            attachment.attach_field(field6)

            message.message_text = "User details"
            message.attach(attachment)
            return message.to_json()
        else:
            print("else")
            return "{0}: {1}".format(r.status_code, r.text)

    def get_my_messages(self,args):
        """Returns the messages of the inbox folder"""
        print("In get_my_messages")
        user_id = self.user_integration.yellowant_integration_id


        get_messages_url = graph_endpoint.format('/me/mailfolders/inbox/messages')

        # Use OData query parameters to control the results
        #  - Only first 10 results returned
        #  - Only return the ReceivedDateTime, Subject, and From fields
        #  - Sort the results by the ReceivedDateTime field in descending order
        query_parameters = {'$top': '10',
                            '$select': 'receivedDateTime,subject,from',
                            '$orderby': 'receivedDateTime DESC'}

        r = make_api_call('GET', get_messages_url, self.access_token, parameters=query_parameters)
        get_compose_url = "https://graph.microsoft.com/v1.0/me/messages"
        body_prev_request = make_api_call('GET', get_compose_url, self.access_token)


        if (r.status_code == requests.codes.ok):

            r_json = r.json()
            obj1 = r_json["value"]
            print(r_json)
            message = MessageClass()
            for i in range(0, len(obj1)):
                obj = obj1[i]
                id = obj["id"]
                bodyPreview = self.list_messages(args, id = id)

                attachment = MessageAttachmentsClass()
                attachment.title = "Subject"
                attachment.text = str(obj["subject"])

                field1 = AttachmentFieldsClass()
                field1.title = "Received Date Time"
                field1.value = str(obj["receivedDateTime"])
                attachment.attach_field(field1)

                if(bodyPreview!=None):
                    field2 = AttachmentFieldsClass()
                    field2.title = "Body Preview"
                    field2.value = str(bodyPreview)
                    attachment.attach_field(field2)

                from_obj = obj["from"]
                for j in range(0,len(from_obj)):
                    emailAddress = from_obj["emailAddress"]
                    field3 = AttachmentFieldsClass()
                    field3.title = "From"
                    field3.value = emailAddress["name"]
                    attachment.attach_field(field3)

                    field4 = AttachmentFieldsClass()
                    field4.title = "Email Id"
                    field4.value = emailAddress["address"]
                    attachment.attach_field(field4)

                button1 = MessageButtonsClass()
                button1.text = "Forward"
                button1.value = "forward"
                button1.name = "forward"
                button1.command = {
                    "service_application": self.user_integration.yellowant_integration_id,
                    "function_name": "forward_message",
                    "data": {
                        "Message-Id": str(obj["id"])
                    },
                    "inputs": [ "toRecipients", "Message" ]
                }


                attachment.attach_button(button1)

                button2 = MessageButtonsClass()
                button2.text = "Reply"
                button2.value = "Reply"
                button2.name = "Reply"
                button2.command = {
                    "service_application": self.user_integration.yellowant_integration_id,
                    "function_name": "reply",
                    "data": {
                        "Message-Id": str(obj["id"])
                    },
                    "inputs": ["Message"]
                }

                attachment.attach_button(button2)

                message.attach(attachment)
            message.message_text = "Inbox messages are"

            return message.to_json()
        else:
            print(r.text)
            return "{0}: {1}".format(r.status_code, r.text)

    def get_message_byfolder(self,args):
        """This function returns the messages of a particular folder.
        The name of the folder is provided as input by the user.
        If the folder is Empty it returns 'Empty Folder' """
        print("In get_message_byfolder")
        folder_name = args["Folder-Name"]
        folder_name = folder_name.strip()
        folder_name = folder_name.replace(" ", "")
        get_foldermessages_url = graph_endpoint.format('/me/mailfolders/{}/messages'.format(folder_name))

        query_parameters = {'$top': '10',
                            '$select': 'receivedDateTime,subject,from',
                            '$orderby': 'receivedDateTime DESC'}

        r = make_api_call('GET', get_foldermessages_url, self.access_token, parameters=query_parameters)
        print(r.json())
        value = r.json()["value"]
        message = MessageClass()

        if(len(value)==0):
            message.message_text = "Empty Folder"
            return message.to_json()

        if (r.status_code == requests.codes.ok):
            for i in range(0, len(value)):
                obj = value[i]

                id = obj["id"]
                bodyPreview = self.list_messages(args, id=id)

                attachment = MessageAttachmentsClass()
                attachment.title = "Subject"
                attachment.text = str(obj["subject"])

                field1 = AttachmentFieldsClass()
                field1.title = "Received Date Time"
                field1.value = str(obj["receivedDateTime"])
                attachment.attach_field(field1)

                if (bodyPreview != None):
                    field2 = AttachmentFieldsClass()
                    field2.title = "Body Preview"
                    field2.value = str(bodyPreview)
                    attachment.attach_field(field2)


                from_obj = obj["from"]
                for j in range(0, len(from_obj)):
                    emailAddress = from_obj["emailAddress"]
                    field3 = AttachmentFieldsClass()
                    field3.title = "From"
                    field3.value = emailAddress["name"]
                    attachment.attach_field(field3)

                    field4 = AttachmentFieldsClass()
                    field4.title = "Email Id"
                    field4.value = emailAddress["address"]
                    attachment.attach_field(field4)

                message.attach(attachment)
                message.message_text = "messages are"
                print("returning mailfolder")
                if(i==len(value)-1):
                    return message.to_json()
                else:
                    continue
        else:
            print(r.text)
            return "{0}: {1}".format(r.status_code, r.text)

    def create_message(self, args):
        """ This function performs two tasks.
        1. It send the message to a draft folder first
        2. When message is saved in the draft folder, the id is extracted and the message is forwarded to
        recipients"""

        print("In create_message")
        get_compose_url = "https://graph.microsoft.com/v1.0/me/messages"
        from_recepients = self.args["toRecipients"]
        from_recepients = from_recepients.split(',')
        for i in range(0, len(from_recepients)):
            print(from_recepients[i])
            data = {
                "subject": self.args["Subject"],
                "importance": "Low",
                "body": {
                    "contentType": "HTML",
                    "content": self.args["body"]
                },
                "toRecipients": [
                    {
                        "emailAddress": {
                            "address": from_recepients[i]
                        }
                    }
                ]
            }
            r = make_api_call('POST', get_compose_url, self.access_token, payload = data)
            print(r.status_code)
            if (r.status_code == 201):
                r_json = r.json()
                message_id = r_json["id"]
                get_send_url = "https://graph.microsoft.com/v1.0/me/messages/{}/send".format(message_id)
                r = make_api_call('POST', get_send_url, self.access_token)
                print("sent is")
                print(r.status_code)
                if(r.status_code == 202):
                    if(i==len(from_recepients)-1):
                        message = MessageClass()
                        message.message_text = "Sent Successfully"
                        return message.to_json()
                    else:
                        print("In continue")
                        continue
                else:
                    return "{0}: {1}".format(r.status_code, r.text)
            else:
                return "{0}: {1}".format(r.status_code, r.text)

    def list_messages(self, args, id=None):
        """List all the messages in the users account(including the Deleted Items and Clutter folders).
            This functions checks for message id and passes the bodyPreview"""
        print("In list_messages")
        get_compose_url = "https://graph.microsoft.com/v1.0/me/messages"
        r = make_api_call('GET', get_compose_url, self.access_token)
        if (r.status_code == 200):
            r_json = r.json()
            data = r_json["value"]
            for i in range(0,len(data)):
                obj = data[i]
                if(id == obj["id"]):
                    return obj["bodyPreview"]
                else:
                    continue;
        else:
            return "{0}: {1}".format(r.status_code, r.text)

    def forward_message(self, args):
        """Forwards a message"""
        print("In forward_message")
        msg_id = args["Message-Id"]
        to_recepients = self.args["toRecipients"]
        message = args["Message"]
        to_recepients = to_recepients.split(',')
        get_forward_url = graph_endpoint.format('/me/messages/{}/forward'.format(msg_id))
        for i in range(0, len(to_recepients)):

            data = {
                "comment": message,
                "toRecipients": [
                    {
                        "emailAddress": {
                            "address": to_recepients[i]
                        }
                    }
                ]
            }
            r = make_api_call('POST', get_forward_url, self.access_token, payload=data)
            if(r.status_code == 202):
                if (i == len(to_recepients) - 1):
                    message = MessageClass()
                    message.message_text = "Forwarded Successfully"
                    return message.to_json()
                else:
                    print("In continue")
                    continue
            else:
                return "{0}: {1}".format(r.status_code, r.text)

    def reply(self, args):
        """Reply to the user with a message"""
        print("In reply")
        msg_id = args["Message-Id"]
        message = args["Message"]
        get_reply_url = graph_endpoint.format('/me/messages/{}/reply'.format(msg_id))
        data = {
            "comment": message
        }
        r = make_api_call('POST', get_reply_url, self.access_token, payload=data)
        if (r.status_code == 202):
            message = MessageClass()
            message.message_text = "Replied Successfully"
            return message.to_json()
        else:
            return "{0}: {1}".format(r.status_code, r.text)

