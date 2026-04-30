from django.db import models
from django.utils import timezone

from .provider import Provider


class AvailabilitySlot(models.Model):
    provider = models.ForeignKey(
        Provider,
        on_delete=models.CASCADE,
        related_name="availability_slots",
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_booked = models.BooleanField(default=False)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["start_time"]
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "start_time", "end_time"],
                name="unique_provider_availability_slot",
            )
        ]

    def __str__(self) -> str:
        start_local = timezone.localtime(self.start_time).strftime("%Y-%m-%d %I:%M %p")
        end_local = timezone.localtime(self.end_time).strftime("%I:%M %p")
        return f"{self.provider} | {start_local} - {end_local}"
