from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.urls import reverse
from django.template import RequestContext
from django.apps import apps
import hmac, base64, hashlib, binascii, os
import shopify


@csrf_exempt
def _new_session(shop_url):
    api_version = apps.get_app_config('shopify_app').SHOPIFY_API_VERSION
    return shopify.Session(shop_url, api_version)

# Ask user for their ${shop}.myshopify.com address

@csrf_exempt
def login(request):

    print("Login")

    if request.GET.get('shop'):
        return authenticate(request)
    
    return render(request, 'shopify_app/login.html', {})


@csrf_exempt
def authenticate(request):

    shop_url = request.GET.get('shop', request.POST.get('shop')).strip()

    print("SHOP URL: ",shop_url)

    if not shop_url:
        messages.error(request, "A shop param is required")
        return redirect(reverse(login))
    
    scope = apps.get_app_config('shopify_app').SHOPIFY_API_SCOPE
    redirect_uri = request.build_absolute_uri(reverse(finalize))

    print("REDIRECT URI: ",redirect_uri)
    
    state = binascii.b2a_hex(os.urandom(15)).decode("utf-8")
    request.session['shopify_oauth_state_param'] = state

    permission_url = _new_session(shop_url).create_permission_url(scope, redirect_uri, state)

    return redirect(permission_url)

@csrf_exempt
def finalize(request):

    print("finalize")

    api_secret = apps.get_app_config('shopify_app').SHOPIFY_API_SECRET
    print("api_secret: ",api_secret)
    params = request.GET.dict()

    if request.session['shopify_oauth_state_param'] != params['state']:
        messages.error(request, 'Anti-forgery state token does not match the initial request.')
        return redirect(reverse(login))
    else:
        request.session.pop('shopify_oauth_state_param', None)

    myhmac = params.pop('hmac')
    line = '&'.join([
        '%s=%s' % (key, value)
        for key, value in sorted(params.items())
    ])
    h = hmac.new(api_secret.encode('utf-8'), line.encode('utf-8'), hashlib.sha256)
    if hmac.compare_digest(h.hexdigest(), myhmac) == False:
        messages.error(request, "Could not verify a secure login")
        return redirect(reverse(login))

    try:
        shop_url = params['shop']
        session = _new_session(shop_url)
        access_token = session.request_token(request.GET)
        request.session['shopify'] = {
            "shop_url": shop_url,
            "access_token": access_token
        }
        # Print the access token to the console
        print(f"Access Token: {access_token}")
    except Exception:
        messages.error(request, "Could not log in to Shopify store.")
        return redirect(reverse(login))
    messages.info(request, "Logged in to Shopify store.")
    request.session.pop('return_to', None)

    return redirect(request.session.get('return_to', reverse('root_path')))

def logout(request):
    request.session.pop('shopify', None)
    messages.info(request, "Successfully logged out.")
    return redirect(reverse(login))
