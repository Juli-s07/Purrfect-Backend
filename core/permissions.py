from rest_framework.permissions import SAFE_METHODS, BasePermission

class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user and request.user.is_staff

class IsBreederOrAdminOrReadOnly(BasePermission):
    # чи є дозвіл на метод
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        u = request.user
        return u.is_authenticated and (u.is_staff or hasattr(u, "breeder"))

    # чи є дозвіл на саме цей ресурс (заводчики змінюються лише свої пости)
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS or request.user.is_staff:
            return True
        breeder = getattr(request.user, "breeder", None)
        return breeder is not None and obj.breeder_id == breeder.id

class IsOwnerBreederOrAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        u = request.user
        return u.is_authenticated and (u.is_staff or hasattr(u, "breeder"))

    # заводчики змінюють лише свої профілі
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS or request.user.is_staff:
            return True
        return obj.user_id == request.user.id
