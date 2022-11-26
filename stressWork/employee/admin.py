from django.contrib import admin
from employee.models import Employee, Topic, Company

# Register your models here.
admin.site.register(Employee)
admin.site.register(Topic)
admin.site.register(Company)
