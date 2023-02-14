from django.urls import path
from .views import CreateFollowingUpView


app_name = 'following'

urlpatterns = [
    path('create/', CreateFollowingUpView.as_view(), name='create_following'),
]
