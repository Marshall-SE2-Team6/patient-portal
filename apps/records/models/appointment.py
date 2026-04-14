from django.db import models
from django.conf import settings


class Appointment(models.Model):
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='appointments')
    doctor_name = models.CharField(max_length=100)
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    reason = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=50, default='Pending')

    def __str__(self):
        return f"{self.patient} - {self.appointment_date} {self.appointment_time}"