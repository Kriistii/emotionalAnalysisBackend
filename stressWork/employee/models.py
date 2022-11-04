from django.db import models

class Employee(models.Model):
    name = models.CharField(max_length=50)
    surname = models.CharField(max_length=50)
    birthday = models.DateField()

    def __str__(self) -> str:
        return f"{self.name + self.surname}"

class Record(models.Model):
    dateTime = models.DateTimeField()
    score = models.IntegerField()
    employee = models.ForeignKey("Employee", on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.dateTime + ' score: ' + self.score}"

