from django.urls import path
from fcm_django.api.rest_framework import FCMDeviceViewSet, FCMDeviceAuthorizedViewSet
from .views import *
from .consumers import *

employee_api = EmployeeAPIView.as_view()
employee_create = CreateEmployeeAPIView.as_view()
employer_create = CreateEmployerAPIView.as_view()
employee_detail_api = EmployeeDetailAPIView.as_view()
timer_chat_over = TimeChatOverEmployee.as_view()
retrieve_sessions_employee = RetrieveSessionsEmployee.as_view()
retrieve_chat_logs_employee = RetrieveChatLogsEmployee.as_view()

retrieve_employee_information = RetrieveEmployeeInformation.as_view()
retrieve_employer_information = RetrieveEmployerInformation.as_view()
test_video_analysis = TestVideoAnalysisAPIView.as_view()

stats = EmployeeStatsAPIView.as_view()
trend = StressStats.as_view()
trendTime = StressStatsTimespan.as_view()
interaction_details = InteractionDetailsAPIView.as_view()

newEmployee = NewEmployee.as_view()
new_session = NewSession.as_view()
interactionSummary = GetInteractionSummary.as_view()
userInteractions = GetUserInteractions.as_view()

urlpatterns = [
    path("", employee_api, name="employees"),
    path('register-notif-token/', FCMDeviceAuthorizedViewSet.as_view({'post': 'create'}), name='create_fcm_device'),
    path('retrieveEmployeeInformation', retrieve_employee_information, name="retrieve-employee-information" ),
    path('retrieveEmployerInformation', retrieve_employer_information, name="retrieve-employer-information"),
    path('timerChatOver', timer_chat_over, name="timer_chat_over"),
    path("testVideoAnalysis", test_video_analysis, name="test-video-analysis"),
    path("getAnalysis/<uuid:chat_id>", interaction_details, name="interaction_details"),
    path("createEmployee", employee_create, name="employee-create"),
    path("createEmployer", employer_create, name="employer-create"),
    path("retrieveSessionsEmployee", retrieve_sessions_employee, name="retrieve_sessions_employee"),
    path("retrieveChatLogsEmployee", retrieve_chat_logs_employee, name="retrieve_chat_logs_employee"),
    path("<int:employee_id>", employee_detail_api, name="employee-detail"),
    path("newSession", new_session, name="new_session"),
    path("backoffice", stats, name="stats"),
    path("trend", trend, name="trend"),
    path("trend/<str:timespan>", trendTime, name="trendTime"),
    path("newEmployee", newEmployee, name="newEmployee"),
    path("getInteractionSummary", interactionSummary, name="interactionSummary"),
    path("getInteractions/<int:employee_id>", userInteractions, name="userInteractions"),
]

