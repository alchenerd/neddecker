from django.urls import include, path
from . import views
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'api/index', views.TopFiveMetaDecksViewSet)

app_name = 'play'
urlpatterns = [
        path("", views.index, name="index"),
        path("play/", views.play, name="play"),
        path("chat/<str:deck_name>", views.chat, name="chat"),
        path("api/", include(router.urls)),
]
urlpatterns += router.urls
