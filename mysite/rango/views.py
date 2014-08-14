from django.shortcuts import render
from django.http import HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response
from rango.models import Category
from rango.models import Page
from rango.models import UserProfile
from rango.forms import CategoryForm
from rango.forms import PageForm
from rango.forms import UserForm, UserProfileForm
from django.contrib.auth import authenticate, login
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import logout
from datetime import datetime
from rango.bing_search import run_query
from django.shortcuts import redirect


def encode_url(str):
    return str.replace(' ', '_')

def decode_url(str):
    return str.replace('_', ' ')

def get_category_list(max_results=0):
	cat_list=[]
	
	cat_list=Category.objects.all()
	
	if max_results > 0:
		if (len(cat_list)) > max_results:
			cat_list = cat_list[:max_results]
	
	for cat in cat_list:
		cat.url = encode_url(cat.name)			
	
	return cat_list

# Create your views here.

#def index(request):
#    return HttpResponse("Rango says hello world! <a href='/rango/about'>About</a>")
    
def about(request):
	context = RequestContext(request)
	
	context_dict = {}
	cat_list = get_category_list()
	context_dict['cat_list'] = cat_list
	
	if request.session.get('visits'):
		count = request.session.get('visits')
	else:
		count = 0
	

	context_dict['visits'] = count
	
	# remember to include the visit data
	return render_to_response('rango/about.html', context_dict, context)

	
def index(request):
    #request.session.set_test_cookie() - See cookies in action. Set cookie to test if received in register()
    # Request the context of the request.
    # The context contains information such as the client's machine details, for example.
    context = RequestContext(request)
    context_dict = {}

    # Construct a dictionary to pass to the template engine as its context.
    # Note the key boldmessage is the same as {{ boldmessage }} in the template!
    #context_dict = {'boldmessage': "I am bold font from the context"}
    
		#Get category list
    cat_list = get_category_list()
    context_dict['cat_list'] = cat_list
	
    # Query the database for a list of ALL categories currently stored.
    # Order the categories by no. likes in descending order.
    # Retrieve the top 5 only - or all if less than 5.
    # Place the list in our context_dict dictionary which will be passed to the template engine.
    category_list = Category.objects.order_by('-likes')[:5]
    context_dict['categories'] = category_list

    # Query the database for a list of ALL pages currently stored.
    # Order the categories by no. likes in descending order.
    # Retrieve the top 5 only - or all if less than 5.
    # Place the list in our context_dict dictionary which will be passed to the template engine.
    pages_list = Page.objects.order_by('-views')[:5]
    context_dict['pages']= pages_list

    # The following two lines are new.
    # We loop through each category returned, and create a URL attribute.
    # This attribute stores an encoded URL (e.g. spaces replaced with underscores).
    for category in category_list:
        category.url = encode_url(category.name)

#	    #### NEW CODE ####
#    # Obtain our Response object early so we can add cookie information.
#    response = render_to_response('rango/index.html', context_dict, context)
#    
#    # Get the number of visits to the site.
#    # We use the COOKIES.get() function to obtain the visits cookie.
#    # If the cookie exists, the value returned is casted to an integer.
#    # If the cookie doesn't exist, we default to zero and cast that.
#    visits = int(request.COOKIES.get('visits', '0'))
#    
#    # Does the cookie last_visit exist?
#    if 'last_visit' in request.COOKIES:
#        # Yes it does! Get the cookie's value.
#        last_visit = request.COOKIES['last_visit']
#        # Cast the value to a Python date/time object.
#        last_visit_time = datetime.strptime(last_visit[:-7], "%Y-%m-%d %H:%M:%S")
#    
#        # If it's been more than a day since the last visit...
#        if (datetime.now() - last_visit_time).days > 0:
#            # ...reassign the value of the cookie to +1 of what it was before...
#            response.set_cookie('visits', visits+1)
#            # ...and update the last visit cookie, too.
#            response.set_cookie('last_visit', datetime.now())
#    else:
#        # Cookie last_visit doesn't exist, so create it to the current date/time.
#        response.set_cookie('last_visit', datetime.now())
#
#     #Return response back to the user, updating any cookies that need changed.
#    return response
    #### END NEW CODE ####		

        #### NEW CODE ####
	if request.session.get('last_visit'):

            # The session has a value for the last visit
            last_visit_time = request.session.get('last_visit')
            visits = request.session.get('visits', 0)
            if (datetime.now() - datetime.strptime(last_visit_time[:-7], "%Y-%m-%d %H:%M:%S")).seconds > 5:
                request.session['visits'] = visits + 1
                request.session['last_visit'] = str(datetime.now())
            else:
            # The get returns None, and the session does not have a value for the last visit.
                request.session['last_visit'] = str(datetime.now())
                request.session['visits'] = 1
	#### END NEW CODE ####
	
	# Return a rendered response to send to the client.
	# We make use of the shortcut function to make our lives easier.
	# Note that the first parameter is the template we wish to use.
    return render_to_response('rango/index.html', context_dict, context)

def category(request,category_name_url):
	context = RequestContext(request)

    # Change underscores in the category name to spaces.
    # URLs don't handle spaces well, so we encode them as underscores.
    # We can then simply replace the underscores with spaces again to get the name.
	category_name = decode_url(category_name_url)
	

    # Create a context dictionary which we can pass to the template rendering engine.
    # We start by containing the name of the category passed by the user.
	context_dict = {'category_name': category_name, 'category_name_url': category_name_url}

	try:
        # Can we find a category with the given name?
        # If we can't, the .get() method raises a DoesNotExist exception.
        # So the .get() method returns one model instance or raises an exception.
		category = Category.objects.get(name=category_name)

        # Retrieve all of the associated pages.
        # Note that filter returns >= 1 model instance.
		pages = Page.objects.filter(category=category)

        # Adds our results list to the template context under name pages.
		context_dict['pages'] = pages
        # We also add the category object from the database to the context dictionary.
        # We'll use this in the template to verify that the category exists.
		context_dict['category'] = category
	except Category.DoesNotExist:
        # We get here if we didn't find the specified category.
        # Don't do anything - the template displays the "no category" message for us.
		pass

	cat_list = get_category_list()
	context_dict['cat_list'] = cat_list

    # Go render the response and return it to the client.
	return render_to_response('rango/category.html', context_dict, context)

@login_required
def add_category(request):
    # Get the context from the request.
    context = RequestContext(request)
    context_dict = {}
    cat_list = get_category_list()
    context_dict['cat_list'] = cat_list

    # A HTTP POST?

    if request.method == 'POST':
        form = CategoryForm(request.POST)
		# Have we been provided with a valid form?
        if form.is_valid():
            # Save the new category to the database.
			form.save(commit=True)
			
            # Now call the index() view.
            # The user will be shown the homepage.
			return index(request)
        else:
            # The supplied form contained errors - just print them to the terminal.
            print form.errors
    else:
        # If the request was not a POST, display the form to enter details.
        form  = CategoryForm()
		
    context_dict['form'] = form

    result_list = []

    if request.method == 'POST':
        query = request.POST['query'].strip()

        if query:
        # Run our Bing function to get the results list!
            result_list = run_query(query)

            context_dict['result_list'] = result_list

    # Bad form (or form details), no form supplied...
    # Render the form with error messages (if any).
    return render_to_response('rango/add_category.html', context_dict, context)
	


@login_required
def add_page(request,category_name_url):
	
	context = RequestContext(request)
	
	category_name = decode_url(category_name_url)
	
	if request.method == 'POST':
		form = PageForm(request.POST)
		
		if form.is_valid():
			# We cannot commit straight away.
			# Not all fields are automatically populated
			
			page = form.save(commit=False)
			
			# Retrieve associated Category object so that we can add it.
			# Wrap the code in a try block - check if the category exists.
			
			try:
				cat=Category.objects.get(name=category_name)
				page.category = cat
			except	Category.DoesNotExist:
				# Case where category does not exist.
				# Go  back and render category and ask for it again.
				return render_to_response('rango/add_category.html',{},context)
			
			#Create default value for the number of views
			page.views=0
			
			#Save our new model instance
			page.save()
			
			#Now that the page is saved, return category instead.
			return category(request, category_name_url)
		
		else:
			print form.errors
	
	else:
		form= PageForm()
		
	
	return render_to_response ('rango/add_page.html',
				   {'category_name_url' : category_name_url,
				    'category_name' : category_name, 'form' : form},
				   context)
	

def register(request):
	#if request.session.test_cookie_worked():
	#	print ">>>> TEST COOKIE WORKED!" -> Lines to test if cookies are working
	#	request.session.delete_test_cookie()
	#Get the request's context.
	context = RequestContext(request)
	
	# A boolean value for telling the template whether the registration was successful.
	# Set to False initially. Code changes value to True when registration succeeds.
	registered = False
	
	#if HTTP post, we're interested in processing form data
	if request.method == 'POST':
		#Attempt to grab info from the raw form information
		# Making use of both User and UserProfile form
		user_form = UserForm(data=request.POST)
		profile_form = UserProfileForm(data=request.POST)
		
		#iF they are valid
		if user_form.is_valid() and profile_form.is_valid():
			#Save user's form data to the database.
			user = user_form.save()
			
			#Hash password with set_password method.
			#Once hashed, we can update user object
			user.set_password(user.password)
			user.save()
			
			#Sort the user profile instance.
			#Since it needs to be setted, committed is set to False
			#This delays savings until it's ready avoiding integrity problems
			
			profile=profile_form.save(commit=False)
			profile.user = user
			
			#Check if user provided picture. If so get it from input form and put it in the profile
			if 'picture' in request.FILES:
				profile.picture = request.FILES['picture']
				
			#Save the user profile model instance
			profile.save()
			
			#Update variable to tell the template registration was successful.
			registered = True
			
		#Invalid form or forms
		#Print problems to the terminal and shown to user
		else:
			print user_form.errors, profile_form.errors
	
	#Not a HTTP post, render form using two ModelForm instances
	#Forms will be blanck, ready for user input
	else:
		user_form=UserForm()
		profile_form=UserProfileForm()
	
	#Render template depending on context
	return render_to_response(
		'rango/register.html',
		{'user_form': user_form, 'profile_form': profile_form, 'registered': registered},
		context)

def user_login(request):
	context = RequestContext(request)
	
	if request.method == 'POST':
		username = request.POST['username']
		password = request.POST['password']
		
		
		 # Use Django's machinery to attempt to see if the username/password
		 # combination is valid - a User object is returned if it is.
		user = authenticate(username=username, password=password)
		
		# If we have a User object, the details are correct.
		# If None (Python's way of representing the absence of a value), no user
		# with matching credentials was found.
		
		if user:
			#check if account is active.
			if user.is_active:
				#if is valid and active the login should proceed.
				#In that case user is sent back to homepage
				login(request,user)
				return HttpResponseRedirect('/rango/')
			else:
				#if innactive account, no login performed
				return HttpResponse('Your Rango account is disabled')
		else:
			#invalid details. no log in
			print "Invalid login details:{0},{1}".format(username,password)
			return HttpResponse('Invalid login details supplied.')
		
	#Not HTTP Post. display login form. Most likely a HTTP GET.
	else:
		return render_to_response('rango/login.html',{},context)

 #decorator
#Note that to use a decorator, you place it directly above the function signature,
#and put a @ before naming the decorator.
#Python will execute the decorator before executing the code of your function/method.
@login_required
def restricted(request):
	context = RequestContext(request)
	return render_to_response('rango/restricted.html',{},context)

@login_required
def user_logout(request):
	#since we know the user is logged in, we just log them out.
	logout(request)
	return HttpResponseRedirect('/rango/')

def search(request):
	context = RequestContext(request)
	result_list = []
	
	if request.method == 'POST':
		query = request.POST['query'].strip()
		
		if query:
			# Run our Bing function to get the results list!
			result_list = run_query(query)

	return render_to_response('rango/search.html', {'result_list': result_list}, context)

def like_count():
    pass

@login_required
def profile(request):
    context = RequestContext(request)
    cat_list = get_category_list()
    context_dict = {'cat_list': cat_list}
    user=User.objects.get(username=request.user)

    try:
        up = UserProfile.objects.get(user=user)
    except:
        up = None

    print up

    context_dict['user'] = user
    context_dict['userprofile'] = up
    return render_to_response('rango/profile.html', context_dict, context)

def track_url(request):
    context = RequestContext(request)
    page_id = None
    url = '/rango/'
    if request.method == 'GET':
        if 'page_id' in request.GET:
            page_id = request.GET['page_id']
            try:
                page = Page.objects.get(id=page_id)
                page.views = page.views + 1
                page.save()
                url = page.url
            except:
                pass

    return redirect(url)




