from django.db import models

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
        return f"{self.provider} | {self.start_time} - {self.end_time}"