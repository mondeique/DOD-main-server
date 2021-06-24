from django.shortcuts import render
from django.http import HttpResponseRedirect
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import viewsets, mixins, status
from rest_framework.views import APIView

from accounts.models import User
from .forms import PostForm


def reset_pw(request):
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


class AutoSendLeftMMS(APIView):
    # TODO 외부 서버에서 crontab 또는 Cloudwatch 로 요청
    def post(self, request, *args, **kwargs):
        return Response(status=status.HTTP_200_OK)