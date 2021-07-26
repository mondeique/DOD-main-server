from rest_framework.permissions import BasePermission


class BoardViewPermission(BasePermission):
    """
    BoardViewSet의 Permission을 위해 만들었습니다.
    create, update, destroy 등은 IsAuthenticated / retrieve, list 등은 AllowAny
    """
    def has_permission(self, request, view):
        if view.action in ['retrieve', 'list']:
            return True
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if view.action in ['retrieve', 'list']:
            return True
        return bool(request.user and request.user.is_authenticated)
