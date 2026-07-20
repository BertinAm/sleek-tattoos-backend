from django.db import models


class Artist(models.Model):
    slug = models.SlugField(max_length=160, unique=True)
    name = models.CharField(max_length=120)
    role = models.CharField(max_length=120, default='Tattoo Artist')
    specialty = models.CharField(max_length=160, blank=True)
    bio = models.TextField(blank=True)
    portrait = models.CharField(max_length=500, blank=True, help_text='Unsplash photo ID or an uploaded image URL')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class NewsPost(models.Model):
    CATEGORY_CHOICES = [('News', 'News'), ('Guest Spot', 'Guest Spot')]

    slug = models.SlugField(max_length=200, unique=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='News')
    title = models.CharField(max_length=200)
    date = models.DateField()
    image = models.CharField(max_length=500, blank=True)
    excerpt = models.TextField(blank=True)
    body = models.TextField(blank=True)
    author = models.CharField(max_length=120, default='Sleek Tattoos Team')
    tags = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return self.title


class GalleryItem(models.Model):
    category = models.CharField(max_length=80)
    title = models.CharField(max_length=160)
    image = models.CharField(max_length=500)
    artist = models.ForeignKey(Artist, null=True, blank=True, on_delete=models.SET_NULL, related_name='gallery_items')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} ({self.category})'


class Service(models.Model):
    name = models.CharField(max_length=160)
    price_label = models.CharField(max_length=80, help_text='Display string, e.g. "₹1,500 starting" or "Custom Quote"')
    description = models.TextField(blank=True)
    examples = models.JSONField(default=list, blank=True)
    cart_value = models.PositiveIntegerField(default=0, help_text='0 means "quote only" (no fixed cart price)')
    image = models.CharField(max_length=500, blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.name


class AboutOccasion(models.Model):
    """The "We're available for" tag list on the About page."""
    label = models.CharField(max_length=120)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.label


class AboutBookingOption(models.Model):
    """The icon-card grid ("Single Tattoo", "Couple Tattoos", ...) on the About page."""
    icon = models.CharField(max_length=60, default='Sparkles', help_text='lucide-react icon name, PascalCase')
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.name


class FAQ(models.Model):
    question = models.CharField(max_length=300)
    answer = models.TextField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'

    def __str__(self):
        return self.question
