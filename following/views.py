from django.views.generic.edit import CreateView
from django.contrib.messages.views import SuccessMessageMixin

from .models import FollowingUp
from .forms import FollowingUpForm


class CreateFollowingUpView(SuccessMessageMixin, CreateView):
    model = FollowingUp
    form_class = FollowingUpForm
    template_name = "following/create.html"
    success_url = '/'
    success_message = 'A follow up is added successfully'
    extra_context = {
        'title': 'Add Following Up'
    }
