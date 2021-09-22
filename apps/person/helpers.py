from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import get_user_model
from django.conf import settings

UserModel = get_user_model()


class AuthBackend(ModelBackend):
    """
    Login w/h username, msisdn or email
    If :msisdn or :email not verified only can use :username
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)

        # Login with username, email or msisdn
        obtain = Q(username__iexact=username) \
            | Q(email__iexact=username) & Q(is_email_verified=True) \
            | Q(msisdn__iexact=username) & Q(is_msisdn_verified=True)

        try:
            # user = UserModel._default_manager.get_by_natural_key(username)
            # You can customise what the given username is checked against, here I compare to both username and email fields of the User model
            user = UserModel.objects.filter(obtain)
        except UserModel.DoesNotExist:
            # Run the default password tokener once to reduce the timing
            # difference between an existing and a nonexistent user (#20760).
            UserModel().set_password(password)
        else:
            try:
                user = user.get(obtain)
            except UserModel.MultipleObjectsReturned:
                message = _(
                    "{} has used. "
                    "If this is you, use Forgot Password verify account".format(username))
                raise ValueError(message)
            except UserModel.DoesNotExist:
                return None

            if user and user.check_password(password) and self.user_can_authenticate(user):
                return user
        return super().authenticate(request, username, password, **kwargs)


class Pagination:
    def __init__(self, request, queryset, queryset_paginate, page_num, paginator):
        self.request = request
        self.can_show_all = True
        self.full_result_count = queryset.count()
        self.list_max_show_all = 200
        self.list_per_page = settings.PAGINATION_PER_PAGE
        self.multi_page = True
        self.page_num = page_num
        self.paginator = paginator
        self.queryset = queryset
        self.result_count = queryset_paginate.paginator.count
        self.result_list = queryset_paginate
        self.root_queryset = queryset
        self.show_all = False
        self.show_full_result_count = True


def build_result_pagination(self, _PAGINATOR, serializer):
    result = {
        'offset': _PAGINATOR.offset,
        'limit': _PAGINATOR.limit,
        'total': _PAGINATOR.count,
        'previous': _PAGINATOR.get_previous_link(),
        'next': _PAGINATOR.get_next_link(),
        'results': serializer.data,
    }

    return result
