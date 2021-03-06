"""Main view for the application"""
import json
import uuid
import datetime
import traceback
from uuid import uuid4
from urllib.parse import urlencode
import requests
from django.http import HttpResponseRedirect, HttpResponse
from django.conf import settings
from django.contrib.auth.models import User
from yellowant import YellowAnt
from yellowant.messageformat import MessageClass, MessageAttachmentsClass, MessageButtonsClass
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .models import YellowUserToken, YellowAntRedirectState, AppRedirectState
from .YellowantCommandCenter import CommandCenter



scopes = ['openid',
          'User.Read',
          'Mail.Read',
          'offline_access',
          'Mail.ReadWrite',
          'Mail.Send']

authority = 'https://login.microsoftonline.com'
authorize_url = '{0}{1}'.format(authority, '/common/oauth2/v2.0/authorize?{0}')
token_url = '{0}{1}'.format(authority, '/common/oauth2/v2.0/token')
graph_endpoint = 'https://graph.microsoft.com/v1.0{0}'

def make_api_call(method, url, token, payload=None, parameters=None):
    # Send these headers with all API calls
    headers = {'User-Agent': 'python_tutorial/1.0',
               'Authorization': 'Bearer {0}'.format(token),
               'Accept': 'application/json'}

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

def redirectToYellowAntAuthenticationPage(request):
    # This is the first redirect. It is specified in YellowAnt API Documentation.
    # The YA_OUTH_URL will shown a page, where the user can choose a team account to authenticate
    # After clicking on 'authorize' the user will be taken to YA_REDIRECT_URL
    # along with YA_CLIENT_ID.
    print("In redirectToYellowAntAuthenticationPage")
    subdomain = request.get_host().split('.')[0]
    user = User.objects.get(id=request.user.id)
    state = str(uuid.uuid4())
    YellowAntRedirectState.objects.create(user=user.id, state=state, subdomain=subdomain)
    return HttpResponseRedirect(
        "{}?state={}&client_id={}&response_type=code&redirect_url={}".format(settings.YA_OAUTH_URL,
                                                                             state,
                                                                             settings.YA_CLIENT_ID,
                                                                             settings.YA_REDIRECT_URL
                                                                            )
    )

def yellowantredirecturl(request):
    # The code is extracted from request URL and it is used to get access token json.
    # The YA_REDIRECT_URL point to this function only
    code = request.GET.get('code')
    state = request.GET.get("state")
    yellowant_redirect_state = YellowAntRedirectState.objects.get(state=state)
    user = yellowant_redirect_state.user
    print(settings.YA_REDIRECT_URL)

    y = YellowAnt(app_key=settings.YA_CLIENT_ID, app_secret=settings.YA_CLIENT_SECRET,
                  access_token=None,
                  redirect_uri=settings.YA_REDIRECT_URL)
    access_token_dict = y.get_access_token(code)

    print(access_token_dict)
    access_token = access_token_dict['access_token']
    yellowant_user = YellowAnt(access_token=access_token)
    profile = yellowant_user.get_user_profile()
    user_integration = yellowant_user.create_user_integration()
    ut = YellowUserToken.objects.create(user=user,
                                        yellowant_token=access_token,
                                        yellowant_id=profile['id'],
                                        yellowant_integration_invoke_name=user_integration["user_invoke_name"],
                                        yellowant_integration_id=user_integration['user_application']
                                       )

    return HttpResponseRedirect(settings.SITE_PROTOCOL +f"{yellowant_redirect_state.subdomain}." +
                                settings.SITE_DOMAIN_URL + settings.BASE_HREF +f"integrate_app?id={ut.id}")

def integrate_app_account(request):
    print("In integrate_app_account")
    ut_id = request.GET.get("id")
    print(ut_id)
    ut = YellowUserToken.objects.get(id=ut_id)
    state = str(uuid.uuid4())
    AppRedirectState.objects.create(user_integration=ut, state=state)

    url = ('{}?state={}'.format(settings.OUTLOOK_REDIRECT_URL, state))

    return HttpResponseRedirect(url)


def get_signin_url(request):

  # Build the query parameters for the signin url
  # The redirect_uri in the params define the that once the sign up page is loaded and
  # the user signs in, the user will
  # then be redirected to the redirect_uri stated. This redirect_uri takes this function
  # to gettoken function.
    print("In get_signin_url")
    state = request.GET.get("state")
    params = {
        'client_id': settings.OUTLOOK_CLIENT_ID,
        'redirect_uri': settings.OUTLOOK_REDIRECT,
        'response_type': 'code',
        'scope': ' '.join(str(i) for i in scopes),
        'state': state
    }

    signin_url = authorize_url.format(urlencode(params))
    print(signin_url)
    return HttpResponseRedirect(signin_url)


def gettoken(request):
    # Here we only get the auth_code. This code exchanged with Auth Token
    print("In gettoken")

    auth_code = request.GET['code']
    state = request.GET.get("state")
    AR = AppRedirectState.objects.get(state=state)
    ut = AR.user_integration

    # Make a request to outlook for the access_token.
    post_data = {'grant_type': 'authorization_code',
                 'code': auth_code,
                 'redirect_uri': settings.OUTLOOK_REDIRECT,
                 'scope': ' '.join(str(i) for i in scopes),
                 'client_id': settings.OUTLOOK_CLIENT_ID,
                 'client_secret': settings.OUTLOOK_CLIENT_SECRET
                }

    r = requests.post(token_url, data=post_data)
    # The response will contain token_type, scope, expires_in, ext_expires_in, access_token,
    # refresh_token, id_token

    access_token_dict = r.json()
    # Now we are collecting the variables
    access_token = access_token_dict["access_token"]
    refresh_token = access_token_dict["refresh_token"]
    YellowUserToken.objects.filter(id=ut.id).update(outlook_access_token=access_token,
                                                    outlook_refresh_token=refresh_token,
                                                    token_update=datetime.datetime.utcnow())

    """Now since we have the access token, we will first create a
    subscription for mail for the user"""

    hash_str = str(uuid4())
    hash_str = hash_str.replace("-", "")
    url = settings.BASE_URL + "webhook/" + hash_str + "/"

    graph_endpoint = "https://outlook.office.com/api/v2.0{}"
    get_wehbhook_url = graph_endpoint.format('/me/subscriptions')
    start_time = datetime.datetime.utcnow()+ datetime.timedelta(minutes=4200)
    current_time = datetime.datetime.utcnow()
    list = str(start_time).split(" ")
    first_word = list[0]+"T"
    second_word = list[1]+"Z"
    start_time = str(first_word + second_word)



    data = {
        "@odata.type": "#Microsoft.OutlookServices.PushSubscription",
        "ChangeType": "created,updated",
        "NotificationURL": url,
        "Resource": "me/mailFolders('Inbox')/messages",
        "SubscriptionExpirationDateTime": start_time
    }
    print("making api call")
    webhook_request = make_api_call('POST', get_wehbhook_url, access_token, payload=data)
    print(webhook_request.status_code)
    if webhook_request.status_code == 401:
        YellowUserToken.objects.filter(outlook_access_token=access_token).update(subscription_id=401,
                                                                                 subscription_update=current_time)
    else:
        response_json = webhook_request.json()
        print(response_json)
        print(webhook_request.status_code)
        YellowUserToken.objects.filter(outlook_access_token=access_token).update(subscription_id=response_json["Id"],
                                                                                 subscription_update=current_time)

    #End of subscription creation

    return HttpResponse(' Access token: {0}'.format(access_token))

@csrf_exempt
@require_POST
def webhook(request, hash_str=""):
    print("Inside webhook")
    data = request.body
    if len(data) == 0:
        validationToken = request.GET['validationtoken']
        try:
            print("In try")
            return HttpResponse(validationToken, status=200)
        except:
            validationToken = None
            print("Error occured")
            return HttpResponse(status=400)
    else:
        try:
            message = MessageClass()
            attachment = MessageAttachmentsClass()
            response_json = json.loads(data)
            value_obj = response_json["value"]
            value = value_obj[0]
            SubscriptionId = value["SubscriptionId"]
            ResourceData = value["ResourceData"]
            message_id = ResourceData["Id"]
            ya_user = YellowUserToken.objects.get(subscription_id=SubscriptionId)
            """Make a request to get the message details using message_id"""
            get_message_details = graph_endpoint.format("/me/messages/{}".format(message_id))
            webhook_request = make_api_call('GET', get_message_details, ya_user.outlook_access_token)
            response_json = webhook_request.json()
            subject = response_json["subject"]
            from_user = response_json["from"]
            email_address = from_user["emailAddress"]

            attachment.title = "Subject"
            attachment.text = str(subject)
            message.attach(attachment)

            forward_button = MessageButtonsClass()
            forward_button.text = "Forward"
            forward_button.value = "forward"
            forward_button.name = "forward"
            forward_button.command = {
                "service_application": ya_user.yellowant_integration_id,
                "function_name": "forward_message",
                "data": {
                    "Message-Id": str(message_id)
                },
                "inputs": ["toRecipients", "Message"]
            }
            attachment.attach_button(forward_button)

            reply_button = MessageButtonsClass()
            reply_button.text = "Reply"
            reply_button.value = "Reply"
            reply_button.name = "Reply"
            reply_button.command = {
                "service_application": ya_user.yellowant_integration_id,
                "function_name": "reply",
                "data": {
                    "Message-Id": str(message_id)
                },
                "inputs": ["Message"]
            }
            attachment.attach_button(reply_button)

            message.message_text = "Ola! You got a new E-mail from-" + email_address["name"] + "( " + email_address["address"] + " )"
            yauser_integration_object = YellowAnt(access_token=ya_user.yellowant_token)
            print("Reached here")
            yauser_integration_object.create_webhook_message(requester_application=ya_user.yellowant_integration_id,
                                                             webhook_name="inbox_webhook", **message.get_dict()
                                                             )
            return True

        except YellowUserToken.DoesNotExist:
            return HttpResponse("Not Authorized", status=403)


@csrf_exempt
def yellowant_api(request):
    print("In yellowant_api")
    try:
        data = json.loads(request.POST['data'])
        print(data)
        verification_token = data["verification_token"]
        print(data["args"])
        if verification_token == settings.YA_VERIFICATION_TOKEN:
            print("Token verified and command is sent")
            cc = CommandCenter(data["user"], data["application"],
                               data["function_name"], data["args"]
                              )
            print("Sent")
            return HttpResponse(cc.parse())
        else:
            return HttpResponse(status=403)
    except Exception as e:
        print("In here")
        print(str(e))
        traceback.print_exc()
        return "Error occured"