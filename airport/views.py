

from django.shortcuts import render
from rest_framework import viewsets, mixins
from rest_framework.viewsets import GenericViewSet

from airport.models import Airport, Route, AirplaneType, Airplane, Crew, Flight
from airport.serializers import AirportSerializer, RouteSerializer, AirplaneTypeSerializer, AirplaneSerializer, \
    CrewSerializer, FlightSerializer


class AirportViewSet(mixins.CreateModelMixin,
                     mixins.ListModelMixin,
                     GenericViewSet):
    queryset = Airport.objects.all()
    serializer_class = AirportSerializer


class RouteViewSet(mixins.CreateModelMixin,
                   mixins.ListModelMixin,
                   GenericViewSet):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer


class AirplaneTypeViewSet(mixins.CreateModelMixin,
                          mixins.ListModelMixin,
                          GenericViewSet):
    queryset = AirplaneType.objects.all()
    serializer_class = AirplaneTypeSerializer


class AirplaneViewSet(mixins.CreateModelMixin,
                      mixins.ListModelMixin,
                      GenericViewSet):
    queryset = Airplane.objects.all()
    serializer_class = AirplaneSerializer


class CrewViewSet(mixins.CreateModelMixin,
                  mixins.ListModelMixin,
                  GenericViewSet):
    queryset = Crew.objects.all()
    serializer_class = CrewSerializer


class FlightViewSet(mixins.CreateModelMixin,
                    mixins.ListModelMixin,
                    GenericViewSet):
    queryset = Flight.objects.all()
    serializer_class = FlightSerializer
