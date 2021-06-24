from django.shortcuts import render

from accounts.models import User
from .forms import PostForm


def post_new(request):
    print('asdasdas')
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            phone = form.cleaned_data['phone']
            user = User.objects.get(phone=phone)
            print(user)
    else:
        print('asdasd')
        form = PostForm()
    return render(request, 'staff_pw_change.html',{
        'form': form,
    })
