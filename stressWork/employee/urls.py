from django.urls import path
from fcm_django.api.rest_framework import FCMDeviceViewSet, FCMDeviceAuthorizedViewSet
from .views import EmployeeAPIView, EmployeeDetailAPIView, NewRecordAPIView, EmployeeStatsAPIView, CloseChatAPIView, StartChatAPIView, StressStats, StressStatsTimespan

employee_api = EmployeeAPIView.as_view()
employee_detail_api = EmployeeDetailAPIView.as_view()
new_record = NewRecordAPIView.as_view()
close_chat = CloseChatAPIView.as_view()
start_chat = StartChatAPIView.as_view()

stats = EmployeeStatsAPIView.as_view()
trend = StressStats.as_view()
trendTime = StressStatsTimespan.as_view()

urlpatterns = [
    path("", employee_api, name="employees"),
    path('register-notif-token/',FCMDeviceViewSet.as_view({'post': 'create'}), name='create_fcm_device'),
    path("<int:employee_id>", employee_detail_api, name="employee-detail"),
    path("newMessage/<int:employee_id>", new_record, name="new_message"),
    path("startChat/<int:employee_id>", start_chat, name="start_chat"),
    path("closeChat", close_chat, name="close_chat"),
    path("backoffice", stats, name="stats"),
    path("trend", trend, name="trend"),
    path("trend/<str:timespan>", trendTime, name="trendTime"),
]