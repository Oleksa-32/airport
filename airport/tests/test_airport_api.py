import os
import tempfile
from datetime import timedelta, datetime

from PIL import Image
from django.contrib.auth import get_user_model
from django.db.models import F, Count
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APIClient

from airport.models import (
    Airport,
    Route,
    AirplaneType,
    Airplane,
    Crew,
    Flight,
    Order,
    Ticket,
)
from airport.serializers import (
    AirportSerializer,
    AirplaneSerializer,
    FlightListSerializer,
)


def sample_airport(name="Test Airport", closest_big_city="Test City"):
    return Airport.objects.create(name=name, closest_big_city=closest_big_city)


def sample_route(source=None, destination=None, distance=100):
    if source is None:
        source = sample_airport(name="Source Airport")
    if destination is None:
        destination = sample_airport(name="Destination Airport")
    return Route.objects.create(
        source=source, destination=destination, distance=distance
    )


def sample_airplane_type(name="Boeing 737"):
    return AirplaneType.objects.create(name=name)


def sample_airplane(name="Test Airplane", rows=10, seats_in_row=6, airplane_type=None):
    if airplane_type is None:
        airplane_type = sample_airplane_type()
    return Airplane.objects.create(
        name=name, rows=rows, seats_in_row=seats_in_row, airplane_type=airplane_type
    )


def sample_crew(first_name="John", last_name="Doe"):
    return Crew.objects.create(first_name=first_name, last_name=last_name)


def sample_flight(
    route=None,
    airplane=None,
    departure_time=None,
    arrival_time=None,
    crew_list=None,
):
    if route is None:
        route = sample_route()
    if airplane is None:
        airplane = sample_airplane()
    if departure_time is None:
        departure_time = timezone.now() + timedelta(days=1)
    if arrival_time is None:
        arrival_time = departure_time + timedelta(hours=2)
    flight = Flight.objects.create(
        route=route,
        airplane=airplane,
        departure_time=departure_time,
        arrival_time=arrival_time,
    )
    if crew_list is None:
        crew_list = [sample_crew()]
    flight.crew.set(crew_list)
    return flight


def sample_order(user, tickets=None):
    order = Order.objects.create(user=user)
    if tickets:
        for ticket in tickets:
            Ticket.objects.create(order=order, **ticket)
    return order


class UnauthenticatedApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_auth_required_airport(self):
        url = reverse("airport:airport-list")
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_auth_required_route(self):
        url = reverse("airport:route-list")
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_auth_required_airplane_type(self):
        url = reverse("airport:airplanetype-list")
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_auth_required_airplane(self):
        url = reverse("airport:airplane-list")
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_auth_required_crew(self):
        url = reverse("airport:crew-list")
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_auth_required_flight(self):
        url = reverse("airport:flight-list")
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_auth_required_order(self):
        url = reverse("airport:order-list")
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedNonAdminTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user("user@example.com", "testpass")
        self.client.force_authenticate(self.user)

    def test_list_airports(self):
        sample_airport(name="Airport 1")
        sample_airport(name="Airport 2")
        url = reverse("airport:airport-list")
        res = self.client.get(url)
        airports = Airport.objects.all().order_by("id")
        serializer = AirportSerializer(airports, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_airport_forbidden(self):
        payload = {"name": "New Airport", "closest_big_city": "Big City"}
        url = reverse("airport:airport-list")
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_routes(self):
        sample_route()
        url = reverse("airport:route-list")
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(res.data), 1)

    def test_create_route_forbidden(self):
        source = sample_airport(name="Src")
        destination = sample_airport(name="Dst")
        payload = {"source": source.id, "destination": destination.id, "distance": 500}
        url = reverse("airport:route-list")
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_airplanes(self):
        sample_airplane(name="Plane 1", rows=10, seats_in_row=6)
        sample_airplane(name="Plane 2", rows=20, seats_in_row=4)
        url = reverse("airport:airplane-list")
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        airplanes = Airplane.objects.all().order_by("id")
        serializer = AirplaneSerializer(airplanes, many=True)
        self.assertEqual(res.data, serializer.data)

    def test_create_airplane_forbidden(self):
        airplane_type = sample_airplane_type()
        payload = {
            "name": "New Plane",
            "rows": 10,
            "seats_in_row": 6,
            "airplane_type": airplane_type.id,
        }
        url = reverse("airport:airplane-list")
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_flights(self):
        sample_flight()
        url = reverse("airport:flight-list")
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Replicate the view's queryset with annotations
        flights = (
            Flight.objects.all()
            .select_related("route", "airplane")
            .annotate(
                tickets_available=(
                    F("airplane__rows") * F("airplane__seats_in_row") - Count("tickets")
                )
            )
            .order_by("id")
        )
        serializer = FlightListSerializer(flights, many=True)
        self.assertEqual(res.data, serializer.data)

    def test_create_flight_forbidden(self):
        route = sample_route()
        airplane = sample_airplane()
        departure = (timezone.now() + timedelta(days=1)).isoformat()
        arrival = (timezone.now() + timedelta(days=1, hours=2)).isoformat()
        payload = {
            "route": route.id,
            "airplane": airplane.id,
            "departure_time": departure,
            "arrival_time": arrival,
            "crew": [sample_crew().id],
        }
        url = reverse("airport:flight-list")
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_orders_empty(self):
        url = reverse("airport:order-list")
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 0)

    def test_create_order_forbidden(self):
        flight = sample_flight()
        payload = {"tickets": [{"row": 1, "seat": 1, "flight": flight.id}]}
        url = reverse("airport:order-list")
        res = self.client.post(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_filter_airplanes_by_airplane_type(self):
        type1 = sample_airplane_type(name="Type1")
        type2 = sample_airplane_type(name="Type2")
        plane1 = sample_airplane(name="Plane1", airplane_type=type1)
        sample_airplane(name="Plane2", airplane_type=type2)
        url = reverse("airport:airplane-list") + f"?airplane_type={type1.id}"
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["id"], plane1.id)


# --- Admin API Tests ---


class AdminApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.admin = get_user_model().objects.create_user(
            "admin@example.com", "testpass", is_staff=True
        )
        self.client.force_authenticate(self.admin)

    def test_create_airport(self):
        payload = {"name": "Admin Airport", "closest_big_city": "Admin City"}
        url = reverse("airport:airport-list")
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        airport = Airport.objects.get(id=res.data["id"])
        self.assertEqual(airport.name, payload["name"])
        self.assertEqual(airport.closest_big_city, payload["closest_big_city"])

    def test_create_route(self):
        source = sample_airport(name="Source Admin")
        destination = sample_airport(name="Destination Admin")
        payload = {"source": source.id, "destination": destination.id, "distance": 750}
        url = reverse("airport:route-list")
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        route = Route.objects.get(id=res.data["id"])
        self.assertEqual(route.distance, payload["distance"])
        self.assertEqual(route.source.id, source.id)
        self.assertEqual(route.destination.id, destination.id)

    def test_create_airplane_type(self):
        payload = {"name": "Airbus A320"}
        url = reverse("airport:airplanetype-list")
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        airplane_type = AirplaneType.objects.get(id=res.data["id"])
        self.assertEqual(airplane_type.name, payload["name"])

    def test_create_airplane(self):
        airplane_type = sample_airplane_type(name="Embraer")
        payload = {
            "name": "Embraer 190",
            "rows": 15,
            "seats_in_row": 4,
            "airplane_type": airplane_type.id,
        }
        url = reverse("airport:airplane-list")
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        airplane = Airplane.objects.get(id=res.data["id"])
        self.assertEqual(airplane.name, payload["name"])
        self.assertEqual(airplane.rows, payload["rows"])
        self.assertEqual(airplane.seats_in_row, payload["seats_in_row"])
        self.assertEqual(airplane.airplane_type.id, airplane_type.id)
        self.assertEqual(airplane.capacity, payload["rows"] * payload["seats_in_row"])

    def test_create_crew(self):
        payload = {"first_name": "Alice", "last_name": "Smith"}
        url = reverse("airport:crew-list")
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        # Depending on your serializer, the new crew object may or may not return an ID.
        crew = Crew.objects.first()
        self.assertEqual(crew.first_name, payload["first_name"])
        self.assertEqual(crew.last_name, payload["last_name"])

    def test_create_flight(self):
        route = sample_route()
        airplane = sample_airplane()
        departure = (timezone.now() + timedelta(days=1)).isoformat()
        arrival = (timezone.now() + timedelta(days=1, hours=2)).isoformat()
        # For flight creation, we send crew data as a list of dictionaries.
        crew_member = sample_crew(first_name="Bob", last_name="Builder")

        payload = {
            "route": route.id,
            "airplane": airplane.id,
            "departure_time": departure,
            "arrival_time": arrival,
            "crew": [crew_member.id],
        }
        url = reverse("airport:flight-list")
        res = self.client.post(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        flight = Flight.objects.get(id=res.data["id"])
        self.assertEqual(flight.route.id, route.id)
        self.assertEqual(flight.airplane.id, airplane.id)
        self.assertEqual(flight.departure_time.isoformat(), departure)
        self.assertEqual(flight.arrival_time.isoformat(), arrival)
        self.assertEqual(flight.crew.count(), 1)
        self.assertEqual(flight.crew.first().id, crew_member.id)

    def test_create_order_with_tickets(self):
        flight = sample_flight()
        payload = {
            "tickets": [
                {"row": 1, "seat": 1, "flight": flight.id},
                {"row": 2, "seat": 3, "flight": flight.id},
            ]
        }
        url = reverse("airport:order-list")
        res = self.client.post(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        order = Order.objects.get(id=res.data["id"])
        self.assertEqual(order.tickets.count(), 2)

    def test_upload_image_to_airplane(self):
        airplane = sample_airplane()
        url = reverse("airport:airplane-upload-image", args=[airplane.id])
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res = self.client.post(url, {"image": ntf}, format="multipart")
        airplane.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image", res.data)
        self.assertTrue(os.path.exists(airplane.image.path))
        # Clean up the uploaded image file.
        airplane.image.delete()

    def test_upload_image_bad_request(self):
        airplane = sample_airplane()
        url = reverse("airport:airplane-upload-image", args=[airplane.id])
        res = self.client.post(url, {"image": "notimage"}, format="multipart")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_put_airplane_not_allowed(self):
        airplane = sample_airplane()
        url = reverse("airport:airplane-detail", args=[airplane.id])
        payload = {"name": "Updated Name"}
        res = self.client.put(url, payload)
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_airplane_not_allowed(self):
        airplane = sample_airplane()
        url = reverse("airport:airplane-detail", args=[airplane.id])
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
