from django.urls import path
from fcm_django.api.rest_framework import FCMDeviceViewSet, FCMDeviceAuthorizedViewSet
from .views import *
from .consumers import *

employee_api = EmployeeAPIView.as_view()
employee_create = CreateEmployeeAPIView.as_view()
employee_detail_api = EmployeeDetailAPIView.as_view()
new_record = NewRecordAPIView.as_view()
close_chat = CloseChatAPIView.as_view()
start_chat = StartChatAPIView.as_view()
retrieve_employee_information = RetrieveEmployeeInformation.as_view()
test_video_analysis = TestVideoAnalysisAPIView.as_view()

stats = EmployeeStatsAPIView.as_view()
trend = StressStats.as_view()
trendTime = StressStatsTimespan.as_view()
prizes = GetPrizes.as_view()
wheels = GetWheels.as_view()

newEmployer = NewEmployer.as_view()
newPrize = NewPrize.as_view()
newWheel = NewWheel.as_view()

delPrize = DelPrize.as_view()

editPrize = EditPrize.as_view()

urlpatterns = [
    path("", employee_api, name="employees"),
    path('register-notif-token/', FCMDeviceAuthorizedViewSet.as_view({'post': 'create'}), name='create_fcm_device'),
    path('retrieveEmployeeInformation', retrieve_employee_information, name="retrieve-employee-information" ),
    path("testVideoAnalysis", test_video_analysis, name="test-video-analysis"),
    path("createEmployee", employee_create, name="employee-create"),
    path("<int:employee_id>", employee_detail_api, name="employee-detail"),
    path("newMessage/<int:employee_id>", new_record, name="new_message"),
    path("startChat/<int:employee_id>", start_chat, name="start_chat"),
    path("closeChat", close_chat, name="close_chat"),
    path("backoffice", stats, name="stats"),
    path("trend", trend, name="trend"),
    path("trend/<str:timespan>", trendTime, name="trendTime"),
    path("newEmployer", newEmployer, name="newEmployer"),
    path("newPrize/<int:wheel_id>", newPrize, name="newPrize"),
    path("prizes/<int:wheel_id>", prizes, name="prizes"),
    path("delPrize/<int:prize_id>", delPrize, name="delPrize"),
    path("editPrize/<int:prize_id>", editPrize, name="editPrize"),
    path("getWheels", wheels, name="wheels"),
    path("newWheel", newWheel, name="newWheel"),
]

