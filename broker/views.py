from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from sensorsafe_broker.broker.forms import *
from django.contrib.auth.models import User as authUser
from sensorsafe_broker.broker.models import *
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import *
from django.shortcuts import render_to_response
from django.template import RequestContext
import hashlib, random
import json

@login_required
def profile(request):
	request.session.set_expiry(0) # logout when browser is closed.
	try:
		userinfo = UserProfile.objects.get(userID__exact = request.user)
		apiKey = userinfo.apiKey
	except ObjectDoesNotExist:
		apiKey = "API Key doesn't exist."

	return render_to_response('registration/profile.html', { 'profile': userinfo }, context_instance=RequestContext(request))
	


def logout_view(request):
	logout(request)
	return HttpResponseRedirect('/broker/login/')



def register_contributor(request):
	if request.method != 'POST':
		return HttpResponseBadRequest('Not POST request')

	userdata = request.POST

	try:
		newUser = authUser.objects.create_user(userdata['username'], userdata['email'], userdata['password'])
		newUser.first_name = userdata['first_name']
		newUser.last_name = userdata['last_name']
		newUserProfile = UserProfile(userID = newUser, apiKey = userdata['apikey'], isConsumer = False, datastoreAddress = userdata['address']) 
		newUser.save()
		newUserProfile.save()
	except KeyError:
		return HttpResponseBadRequest('Key error in POST data')

	return HttpResponse('Success')



def check_post_request_apikey(postdata):
	if not 'apikey' in postdata:
		return False, None, HttpResponseBadRequest("No 'apikey' in post data")

	try:
		userinfo = UserProfile.objects.get(apiKey__exact = postdata['apikey'])
	except ObjectDoesNotExist:
		return False, None, HttpResponseBadRequest("Bad API key.")

	return True, userinfo, None



def get_consumers(request):
	if request.method != 'POST':
		return HttpResponseBadRequest('Not POST request')

	isSuccess, userinfo, http_response = check_post_request_apikey(request.POST)
	if not isSuccess:
		return http_response

	# get list of consumer usernames
	username_list = []
	for userinfo in UserProfile.objects.select_related().filter(isConsumer=True):
		username_list.append(userinfo.userID.username)

	return HttpResponse(json.dumps(username_list))



def register(request):
	errorMsg = []
	if request.method == 'POST':
		form = UserRegistrationForm(request.POST)

		if form.is_valid():
			error = False
			if form.data['password'] != form.data['confirm_password']:
				errorMsg.append("Password didn't match.")
				error = True
			
			# Make sure username is available and email is not already in system
			isNewUser = False
			try: 
				authUser.objects.get(username__exact=form.data['username'])
			except ObjectDoesNotExist:
			 isNewUser = True

			isNewEmail = False
			try: 
				authUser.objects.get(email__exact=form.data['email'])
			except ObjectDoesNotExist:
				isNewEmail = True

			if not isNewUser:
				errorMsg.append("Existing user name.")
				error = True
			if not isNewEmail:
				errorMsg.append("Existing email address.")
				error = True

			if not error:
				# create a user
				newUser = authUser.objects.create_user(form.data['username'], form.data['email'], form.data['password'])
				newUser.first_name = form.data['first_name']
				newUser.last_name = form.data['last_name']
				newUser.save()

				# generate keys
				apiKey = hashlib.sha1(newUser.username + str(random.random())).hexdigest()
				newUserProfile = UserProfile(userID = newUser, apiKey = apiKey, isConsumer = True) 
				newUserProfile.save()
			
				# log the user in
				logout(request)
				user = authenticate(username=form.data['username'], password=form.data['password'])
				login(request, user)

				return HttpResponseRedirect('/broker/profile/')
	else:
		form = UserRegistrationForm()

	return render_to_response('registration/register.html', { 'form': form, 'errorMsg': errorMsg }, context_instance=RequestContext(request))



@login_required
def display(request):
	userinfo = UserProfile.objects.get(userID__exact = request.user)
	contributor_list = UserProfile.objects.filter(isConsumer = False);
	return render_to_response('display2.html', { 'apikey': userinfo.apiKey, 'contributor_list': contributor_list }, context_instance=RequestContext(request))



def get_username(request):
	if request.method != 'POST':
		return HttpResponseBadRequest('Not POST request')
	
	isSuccess, userinfo, http_response = check_post_request_apikey(request.POST)
	if not isSuccess:
		return http_response

	return HttpResponse(userinfo.userID.username)


@login_required
def search_contributors(request):
	userinfo = UserProfile.objects.get(userID__exact = request.user)
	contributors = UserProfile.objects.filter(isConsumer = False)
	return render_to_response('search_contributors.html', { 'apikey': userinfo.apiKey, 'contributors': contributors }, context_instance=RequestContext(request))



def get_contributors(request):
	if request.method != 'POST':
		return HttpResponseBadRequest('Not POST request')
	
	isSuccess, userinfo, http_response = check_post_request_apikey(request.POST)
	if not isSuccess:
		return http_response

	contributors = UserProfile.objects.filter(isConsumer = False)
	
	contributors_list = []
	for c in contributors:
		contributors_list.append( [c.userID.username, c.datastoreAddress] )
	
	return HttpResponse(json.dumps(contributors_list))
	
