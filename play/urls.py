from django.urls import path
from . import views

app_name = 'play'
urlpatterns = [
        path("", views.index, name="index"),
        path("play/", views.play, name="play"),
        path("chat/<str:deck_name>", views.chat, name="chat"),
]
