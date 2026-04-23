from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.notifications.models import Notification, NotificationStatus


class NotificationModelTests(TestCase):
    def test_mark_as_read_updates_status_and_timestamp(self) -> None:
        user = get_user_model().objects.create_user(
            username="notifuser",
            password="testpass123",
        )

        notification = Notification.objects.create(
            recipient=user,
            message="Test notification message",
        )

        self.assertEqual(notification.status, NotificationStatus.PENDING)
        self.assertIsNone(notification.read_at)

        notification.mark_as_read()
        notification.refresh_from_db()

        self.assertEqual(notification.status, NotificationStatus.READ)
        self.assertIsNotNone(notification.read_at)