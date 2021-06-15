from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet, ProjectDashboardViewSet, PastProjectViewSet

app_name = 'projects'


router = DefaultRouter()
router.register('project', ProjectViewSet, basename='project')
router.register('dashboard', ProjectDashboardViewSet, basename='dashboard')
router.register('past-project', PastProjectViewSet, basename='past-project')

urlpatterns = [
    path('', include(router.urls)),
]