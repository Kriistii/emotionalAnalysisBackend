from django.urls import path
from fcm_django.api.rest_framework import FCMDeviceViewSet, FCMDeviceAuthorizedViewSet
from .views import *
from .consumers import *

employee_api = EmployeeAPIView.as_view()
employee_create = CreateEmployeeAPIView.as_view()
employer_create = CreateEmployerAPIView.as_view()
employee_detail_api = EmployeeDetailAPIView.as_view()
timer_chat_over = TimeChatOverEmployee.as_view()
retrieve_chat_logs_employee = RetrieveChatLogsEmployee.as_view()

retrieve_employee_information = RetrieveEmployeeInformation.as_view()
retrieve_employer_information = RetrieveEmployerInformation.as_view()
test_video_analysis = TestVideoAnalysisAPIView.as_view()

stats = EmployeeStatsAPIView.as_view()
trend = StressStats.as_view()
trendTime = StressStatsTimespan.as_view()
interaction_details = InteractionDetailsAPIView.as_view()

newEmployee = NewEmployee.as_view()
registration_form = RegistrationForm.as_view()
get_step = GetStep.as_view()
new_request = NewRequest.as_view()
new_session = NewSession.as_view()
complete_new_request = CompleteNewRequest.as_view()
questionnaire_request = GetQuestionnaireRequest.as_view()
fill_in_questionnaire = FillInQuestionnaire.as_view()
interactionSummary = GetInteractionSummary.as_view()
userInteractions = GetUserInteractions.as_view()
get_sessions = RetrieveSessionsEmployee.as_view()
tas = TasQuestionnaire.as_view()
bdi = BDIQuestionnaire.as_view()
bai = BAIQuestionnaire.as_view()
ders = DERSQuestionnaire.as_view()
panas = PANASQuestionnaire.as_view()
vas = VasQuestionnaireView.as_view()
tasDownload = downloadTas.as_view()
bdiDownload = downloadBdi.as_view()
baiDownload = downloadBai.as_view()
dersDownload = downloadDers.as_view()
panasDownload = downloadPanas.as_view()


urlpatterns = [
    path("", employee_api, name="employees"),
    path('register-notif-token/', FCMDeviceAuthorizedViewSet.as_view({'post': 'create'}), name='create_fcm_device'),
    path('retrieveEmployeeInformation', retrieve_employee_information, name="retrieve-employee-information" ),
    path('retrieveEmployerInformation', retrieve_employer_information, name="retrieve-employer-information"),
    path('timerChatOver', timer_chat_over, name="timer_chat_over"),
    path("testVideoAnalysis", test_video_analysis, name="test-video-analysis"),
    path("getAnalysis/<uuid:session_id>", interaction_details, name="interaction_details"),
    path("createEmployee", employee_create, name="employee-create"),
    path("createEmployer", employer_create, name="employer-create"),
    path("retrieveChatLogsEmployee", retrieve_chat_logs_employee, name="retrieve_chat_logs_employee"),
    path("<int:employee_id>", employee_detail_api, name="employee-detail"),
    path("newSession", new_session, name="new_session"),
    path("backoffice", stats, name="stats"),
    path("trend", trend, name="trend"),
    path("trend/<str:timespan>", trendTime, name="trendTime"),
    path("newEmployee", newEmployee, name="newEmployee"),
    path("newRequest", new_request, name="newRequest"),
    path("completeNewRequest", complete_new_request, name="completeNewRequest"),
    path("questionnaireRequest", questionnaire_request, name="questionnaireRequest"),
    path("fillInQuestionnaire", fill_in_questionnaire, name="fillInQuestionnaire"),
    path("getInteractionSummary", interactionSummary, name="interactionSummary"),
    path("getInteractions/<int:employee_id>", userInteractions, name="userInteractions"),
    path("getSessions/<int:employee_id>", get_sessions, name="get_sessions"),
    path("getStep", get_step, name="get_step"),
    path("registrationForm", registration_form, name="registration_form"),
    path("tas", tas, name="tas"),
    path("vas", vas, name="vas"),
    path("bdi", bdi, name="bdi"),
    path("bai", bai, name="bai"),
    path("ders", ders, name="ders"),
    path("panas", panas, name="panas"),
    path("tasDownload", tasDownload, name="tasDownload"),
    path("bdiDownload", bdiDownload, name="bdiDownload"),
    path("baiDownload", baiDownload, name="baiDownload"),
    path("panasDownload", panasDownload, name="panasDownload"),
]

