from django.shortcuts import render
from django.http import HttpResponseRedirect
from accounts.models import User
from .forms import PostForm


def post_new(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            phone = form.cleaned_data['phone']
            pw = form.cleaned_data['password']
            user = User.objects.get(phone=phone)
            user.set_password(pw)
            user.save()
            return HttpResponseRedirect("staff/")
    else:
        if request.user.is_anonymous:
            return HttpResponseRedirect("/staff/")
        form = PostForm()
    return render(request, 'staff_pw_change.html',{
        'form': form,
    })
