from django.urls import path, include
from rest_framework import routers

from airport import views

router = routers.DefaultRouter()
router.register('airports', views.AirportViewSet)
router.register("routes", views.RouteViewSet)
router.register("airplane_types", views.AirplaneTypeViewSet)
router.register("airplanes", views.AirplaneViewSet)
router.register("crews", views.CrewViewSet)
router.register("flights", views.FlightViewSet)

urlpatterns = [path("", include(router.urls))]

app_name = 'airport'
