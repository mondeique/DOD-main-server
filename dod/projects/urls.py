from django.urls import path, include
from .routers import router
from rest_framework.routers import DefaultRouter

from .views import ProjectViewSet, ProjectDashboardViewSet

router = DefaultRouter()
router.register('project', ProjectViewSet, basename='project')
router.register('dashboard', ProjectDashboardViewSet, basename='dashboard')

urlpatterns = [
    path('', include(router.urls)),
]