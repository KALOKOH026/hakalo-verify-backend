from rest_framework.permissions import BasePermission, IsAuthenticated


class IsPlatformAdmin(BasePermission):
    """Allow platform administrators only."""

    def has_permission(self, request, view):
        if not isinstance(request.user, object):
            return False
        return bool(request.user and request.user.is_authenticated and getattr(request.user, 'is_staff', False) and getattr(request.user, 'is_superuser', False))


class IsMfiStaff(BasePermission):
    """Allow authenticated MFI staff members for their institution."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if getattr(request.user, 'is_superuser', False):
            return True
        membership = getattr(request.user, 'institution_membership', None)
        return bool(membership and membership.is_active and membership.role in {'MFI_STAFF', 'MFI_ADMIN'})


class IsMfiAdmin(BasePermission):
    """Allow MFI admins for their institution."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if getattr(request.user, 'is_superuser', False):
            return True
        membership = getattr(request.user, 'institution_membership', None)
        return bool(membership and membership.is_active and membership.role == 'MFI_ADMIN')


class IsInstitutionScopedObject(BasePermission):
    """Ensure an object belongs to the requesting user's institution."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return True

    def has_object_permission(self, request, view, obj):
        if getattr(request.user, 'is_superuser', False):
            return True
        membership = getattr(request.user, 'institution_membership', None)
        if not membership or not membership.is_active:
            return False

        if getattr(obj, 'pk', None) is not None and type(obj).__name__ == 'Institution':
            return obj.pk == membership.institution_id
        if hasattr(obj, 'institution'):
            return obj.institution_id == membership.institution_id
        if hasattr(obj, 'requesting_institution'):
            return obj.requesting_institution_id == membership.institution_id
        if hasattr(obj, 'institution_id'):
            return obj.institution_id == membership.institution_id
        return False
