from django.db import models


class Location(models.Model):
    """Powers the booking form's location dropdown and travel-fee lookup."""
    name = models.CharField(max_length=120, unique=True)
    travel_fee = models.PositiveIntegerField(default=0, help_text='0 = free (Law Gate / Phagwara / Jalandhar)')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f'{self.name} (₹{self.travel_fee})' if self.travel_fee else f'{self.name} (FREE)'


class Booking(models.Model):
    STATUS_CHOICES = [('New', 'New'), ('Contacted', 'Contacted'), ('Completed', 'Completed')]
    APPOINTMENT_TYPE_CHOICES = [('Studio Service', 'Studio Service'), ('Home Service', 'Home Service')]
    GENDER_CHOICES = [('Female', 'Female'), ('Male', 'Male'), ('Other', 'Other'), ('Prefer not to say', 'Prefer not to say')]

    name = models.CharField(max_length=160)
    gender = models.CharField(max_length=30, choices=GENDER_CHOICES, blank=True)
    email = models.EmailField()
    country_code = models.CharField(max_length=8, default='+91')
    phone = models.CharField(max_length=20)
    appointment_type = models.CharField(max_length=20, choices=APPOINTMENT_TYPE_CHOICES, default='Studio Service')
    party_size = models.CharField(max_length=60, default='Single (1 person)')
    location = models.CharField(max_length=160)
    preferred_date = models.DateField()
    preferred_time = models.TimeField()
    notes = models.TextField(blank=True)
    reference_images = models.JSONField(default=list, blank=True, help_text='URLs returned by /api/uploads/images/')
    travel_fee = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='New')

    # Google Calendar sync bookkeeping — never blocks booking creation, see
    # bookings/services/google_calendar.py. calendar_sync_error is set (and
    # event id left blank) if the Calendar API call fails for any reason.
    google_calendar_event_id = models.CharField(max_length=200, blank=True, default='')
    calendar_sync_error = models.TextField(blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} — {self.preferred_date} {self.preferred_time} ({self.status})'
