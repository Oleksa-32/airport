

from django.shortcuts import render
from rest_framework import viewsets, mixins
from rest_framework.viewsets import GenericViewSet

from airport.models import Airport, Route, AirplaneType, Airplane, Crew, Flight, Order
from airport.serializers import AirportSerializer, RouteSerializer, AirplaneTypeSerializer, AirplaneSerializer, \
    CrewSerializer, FlightSerializer, OrderSerializer, OrderListSerializer


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


class OrderViewSet(mixins.CreateModelMixin,
                   mixins.ListModelMixin,
                   GenericViewSet):
    queryset = Order.objects.prefetch_related(
        "tickets", "tickets__flight"
    )
    serializer_class = OrderSerializer
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'list':
            return OrderListSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
