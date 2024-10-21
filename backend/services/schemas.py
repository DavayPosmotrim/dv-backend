from drf_spectacular.utils import OpenApiParameter

device_id_header = OpenApiParameter(
    name="Device-Id",
    type=str,
    location=OpenApiParameter.HEADER,
    required=True,
    description="Device-Id пользователя",
)
