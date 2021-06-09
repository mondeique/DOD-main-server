from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet, ProjectDashboardViewSet

app_name = 'projects'


router = DefaultRouter()
router.register('project', ProjectViewSet, basename='project')
router.register('dashboard', ProjectDashboardViewSet, basename='dashboard')

urlpatterns = [
    path('', include(router.urls)),
]