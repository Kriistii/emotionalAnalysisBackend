from django.urls import path

from .views import EmployeeAPIView, EmployeeDetailAPIView, NewRecordAPIView, EmployeeStatsAPIView, CloseChatAPIView

employee_api = EmployeeAPIView.as_view()
employee_detail_api = EmployeeDetailAPIView.as_view()
new_record = NewRecordAPIView.as_view()
close_chat = CloseChatAPIView.as_view()

stats = EmployeeStatsAPIView.as_view()

urlpatterns = [
    path("", employee_api, name="employees"),
    path("<int:employee_id>", employee_detail_api, name="employee-detail"),
    path("newRecording", new_record, name="new_record"),
    path("closeChat", close_chat, name="close_chat"),
    path("backoffice", stats, name="stats")
]