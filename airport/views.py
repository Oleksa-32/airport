from django.db.models import Count, F
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import mixins, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.utils import timezone
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from airport.models import Airport, Route, AirplaneType, Airplane, Crew, Flight, Order
from airport.permissions import IsAdminOrIfAuthenticatedReadOnly
from airport.serializers import (
    AirportSerializer,
    RouteSerializer,
    AirplaneTypeSerializer,
    AirplaneSerializer,
    CrewSerializer,
    FlightSerializer,
    OrderSerializer,
    OrderListSerializer,
    FlightListSerializer,
    FlightDetailSerializer,
    AirplaneDetailSerializer,
    AirplaneImageSerializer,
)


class AirportViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, GenericViewSet):
    queryset = Airport.objects.all()
    serializer_class = AirportSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)


class RouteViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, GenericViewSet):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)


class AirplaneTypeViewSet(
    mixins.CreateModelMixin, mixins.ListModelMixin, GenericViewSet
):
    queryset = AirplaneType.objects.all()
    serializer_class = AirplaneTypeSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)


@extend_schema()
class AirplaneViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet,
):
    queryset = Airplane.objects.all()
    serializer_class = AirplaneSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

    def get_queryset(self):
        queryset = super().get_queryset()

        airplane_type_id = self.request.query_params.get("airplane_type")
        capacity = self.request.query_params.get("min_capacity")

        if airplane_type_id:
            queryset = queryset.filter(airplane_type_id=airplane_type_id)

        if capacity:
            queryset = [plane for plane in queryset if plane.capacity >= int(capacity)]

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return AirplaneSerializer
        if self.action == "retrieve":
            return AirplaneDetailSerializer
        if self.action == "upload_image":
            return AirplaneImageSerializer
        return AirplaneSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="airplane_type",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Filter by airplane_type_id (example: ?airplane_type=2)",
            ),
            OpenApiParameter(
                name="min_capacity",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Filter by seat capacity (example: ?capacity=150)",
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @action(
        methods=["POST"],
        detail=True,
        url_path="upload-image",
        permission_classes=[IsAdminUser],
    )
    def upload_image(self, request, pk=None):
        airplane = self.get_object()
        serializer = self.get_serializer(airplane, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CrewViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, GenericViewSet):
    queryset = Crew.objects.all()
    serializer_class = CrewSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)


@extend_schema(
    parameters=[
        OpenApiParameter(
            name="route_id",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description="Filter flights by exact Route ID. Example: ?route_id=5",
        ),
        OpenApiParameter(
            name="airplane_id",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description="Filter flights by exact AirplaneType ID. Example: ?airplane_id=2",
        ),
        OpenApiParameter(
            name="departure_after",
            type=OpenApiTypes.DATETIME,
            location=OpenApiParameter.QUERY,
            description="Return only flights departing on or after this time. Example: ?departure_after=2025-01-01T10:00:00Z",
        ),
    ]
)
class FlightViewSet(ModelViewSet):
    queryset = (
        Flight.objects.all()
        .select_related("route", "airplane")
        .annotate(
            tickets_available=(
                F("airplane__rows") * F("airplane__seats_in_row") - Count("tickets")
            )
        )
    )
    serializer_class = FlightSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

    def get_queryset(self):
        queryset = self.queryset

        route_id = self.request.query_params.get("route_id")
        airplane_id = self.request.query_params.get("airplane_id")
        departure_after = self.request.query_params.get("departure_after")

        if route_id:
            queryset = queryset.filter(route_id=route_id)

        if airplane_id:
            queryset = queryset.filter(airplane_id=airplane_id)

        if departure_after:
            dep_time = timezone.datetime.fromisoformat(departure_after)
            queryset = queryset.filter(departure_time__gte=dep_time)

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return FlightListSerializer
        if self.action == "retrieve":
            return FlightDetailSerializer
        return FlightSerializer

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class OrderViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, GenericViewSet):
    queryset = Order.objects.prefetch_related("tickets", "tickets__flight")
    serializer_class = OrderSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
