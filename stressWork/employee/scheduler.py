import sys

from apscheduler.schedulers.background import BackgroundScheduler

from .models import Employee, StressRecord

scheduler = BackgroundScheduler()


def save_data():
    stressedEmployees = Employee.objects.filter(stressed=True).count()
    StressRecord.objects.create(stressedUsers=stressedEmployees)


def start():
    # run this job every 24 hours
    scheduler.add_job(save_data, 'interval', hours=24, name='save_data', jobstore='default')
    scheduler.start()
    print("Scheduler started...", file=sys.stdout)
