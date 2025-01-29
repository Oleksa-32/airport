from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from airport.models import (
    Airport,
    Route,
    Airplane,
    Crew,
    Flight,
    Ticket,
    Order,
    AirplaneType,
)


class AirportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airport
        fields = ("id", "name", "closest_big_city")


class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ("id", "source", "destination", "distance")


class AirplaneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airplane
        fields = ("id", "name", "rows", "seats_in_row", "airplane_type")


class AirplaneTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AirplaneType
        fields = ("id", "name")


class CrewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crew
        fields = ("first_name", "last_name")


class FlightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flight
        fields = ("route", "airplane", "departure_time", "arrival_time")


class FlightListSerializer(serializers.ModelSerializer):
    route = serializers.SlugRelatedField(many=True, read_only=True, slug_field="name")
    airplane = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="name"
    )
    tickets_available = serializers.IntegerField(read_only=True)

    class Meta:
        model = Flight
        fields = (
            "route",
            "airplane",
            "departure_time",
            "arrival_time",
            "tickets_available",
        )


class TicketSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        data = super(TicketSerializer, self).validate(attrs=attrs)
        Ticket.validate_ticket(
            attrs["row"], attrs["seat"], attrs["flight"].airplane, ValidationError
        )
        return data

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "flight", "order")


class TicketSeatsSerializer(TicketSerializer):
    class Meta:
        model = Ticket
        fields = ("row", "seat")


class TicketListSerializer(TicketSerializer):
    flight = FlightListSerializer(many=False, read_only=True)


class FlightDetailSerializer(serializers.ModelSerializer):
    route = RouteSerializer(many=True, read_only=True)
    airplane = AirplaneSerializer(many=True, read_only=True)
    taken_places = TicketSeatsSerializer(source="tickets", many=True, read_only=True)

    class Meta:
        model = Flight
        fields = ("route", "airplane", "departure_time", "arrival_time")


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=False, allow_empty=False)

    class Meta:
        model = Order
        fields = ("id", "tickets", "created_at")

    def create(self, validated_data):
        with transaction.atomic():
            ticket_data = validated_data.pop("tickets")
            order = Order.objects.create(**validated_data)
            for ticket_data in ticket_data:
                Ticket.objects.create(order=order, **ticket_data)
            return order


class OrderListSerializer(OrderSerializer):
    tickets = TicketSerializer(many=True, read_only=True)
