from django.urls import path, include
from .routers import router
from .views import ProjectViewSet

router.register('project', ProjectViewSet, basename='project')

urlpatterns = [
    path('', include(router.urls)),
]