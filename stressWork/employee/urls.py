from django.urls import path

from .views import EmployeeAPIView, EmployeeDetailAPIView, NewRecordAPIView

employee_api = EmployeeAPIView.as_view()
employee_detail_api = EmployeeDetailAPIView.as_view()
new_rercoding = NewRecordAPIView.as_view()

urlpatterns = [
    path("", employee_api, name="employees"),
    path("<int:employee_id>", employee_detail_api, name="employee-detail"),
    path("newRecording", new_rercoding, name="new-recording" )
]