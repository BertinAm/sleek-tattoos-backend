"""
Seeds the database with the studio's real (trimmed, curated) content — a
handful of news posts and gallery pieces, all tied to the studio's one
featured artist, plus the full services/pricing list, About copy and FAQ.

Clears NewsPost, Artist and GalleryItem first (so re-running this always
reflects exactly this curated list, not an ever-growing superset) — Service,
AboutOccasion, AboutBookingOption and FAQ use update_or_create instead since
there's no "trim to a few" requirement for those.

Usage: python manage.py seed_content
"""
from datetime import datetime

from django.core.management.base import BaseCommand

from content.models import AboutBookingOption, AboutOccasion, Artist, FAQ, GalleryItem, NewsPost, Service


# A curated handful, not the full back-catalogue — mixed News/Guest Spot for variety.
NEWS_POSTS = [
    dict(slug='tattoo-jam-iv', category='News', title='Tattoo Jam IV: 5 & 6 July', date='6/17/2024',
         image='photo-1611501275019-9b5cda994e8d',
         excerpt="Two days of live tattooing, guest artists and music at our biggest studio event of the year.",
         body="Tattoo Jam IV brings together artists from across India for two days of live sessions, flash drops and a celebration of the craft. Walk-ins are welcome both days, and a handful of guest artists will be joining our resident team for exclusive one-off designs.\n\nExpect flash sheets released each morning, a small food and music setup in the courtyard, and limited-slot bookings for larger custom pieces.",
         author='Sleek Tattoos Team', tags=['Events', 'Flash', 'Studio']),
    dict(slug='walk-in-day', category='News', title='Walk-In Day!', date='4/26/2024',
         image='photo-1598371839696-5c5bb00bdc28',
         excerpt="No appointment needed. Swing by the studio and pick from our flash wall.",
         body="Once a month we open our doors for walk-in-only sessions. No booking required. Just come to Law Gate, browse the flash wall, and get inked the same day, first come first served.\n\nPricing is fixed per flash design so there's no consultation needed.",
         author='Sleek Tattoos Team', tags=['Walk-In', 'Flash']),
    dict(slug='guest-spot-inkbyaria', category='Guest Spot', title='Guest Spot: @inkbyaria', date='1/19/2024',
         image='photo-1611501275019-9b5cda994e8d',
         excerpt="A celebrated black & grey portrait artist joins us for a limited guest residency.",
         body="We're hosting a guest artist known for striking black & grey portrait work for a limited residency at our Law Gate studio. Slots are limited.",
         author='Guest Artist Program', tags=['Guest Spot', 'Black & Grey', 'Portraits']),
    dict(slug='sleek-tattoos-anniversary', category='News', title='Celebrating One Year of Sleek Tattoos', date='8/14/2023',
         image='photo-1598371839696-5c5bb00bdc28',
         excerpt="Looking back at our first year bringing premium tattoo art to India.",
         body="It's been one year since Sleek Tattoos opened its doors as the first African tattoo service in India. Thank you to every client who trusted us with their skin and their story.",
         author='Founder', tags=['Milestones', 'Studio']),
    dict(slug='home-service-expansion', category='News', title='Home Service Now Covers More Cities', date='5/30/2023',
         image='photo-1598371839696-5c5bb00bdc28',
         excerpt="We've expanded home service travel coverage to more cities across India.",
         body="Home service bookings now cover an expanded list of cities across Punjab, Haryana, Delhi NCR and beyond, each with transparent, fixed travel fees.",
         author='Studio Admin', tags=['Home Service', 'Coverage']),
]

# Single featured artist — every gallery piece below ties back to this one slug.
ARTISTS = [
    dict(slug='mateusz-kocjan', name='Mateusz Kocjan', role='Tattoo Artist', specialty='Geometric & Dotwork',
         bio="Always calm and never in a hurry, Mateusz's work strives to find the perfect blend of geometric patterns and shapes with the human form. Every piece is planned around the body's natural lines.",
         portrait='photo-1611501275019-9b5cda994e8d'),
]

GALLERY = [
    ('Fine Line', 'Fine Line Study', 'photo-1566745506472-ace07aeae19f', 'mateusz-kocjan'),
    ('Minimal', 'Minimal Line', 'photo-1627960630431-270d04164a22', 'mateusz-kocjan'),
    ('Anime', 'Anime Inspired', 'photo-1778837224447-8f3b265035eb', 'mateusz-kocjan'),
    ('Black & Grey', 'Black & Grey', 'photo-1562962230-16e4623d36e6', 'mateusz-kocjan'),
    ('Sleeves', 'Full Sleeve', 'photo-1543244128-30d70d41e2a9', 'mateusz-kocjan'),
    ('Custom Work', 'Fully Custom', 'photo-1665085326630-b01fea9a613d', 'mateusz-kocjan'),
]

SERVICES = [
    dict(name='Minimum Tattoo', price_label='₹1,500 starting', description='A tiny, meaningful mark, perfect for a first tattoo.',
         examples=['Initials', 'Small symbol'], cart_value=1500, image='photo-1659615043416-c492e7f4f8ab'),
    dict(name='Tiny Tattoos (1 to 2 in)', price_label='₹1,500 starting', description='Delicate fine-line work for small, personal designs.',
         examples=['Initials', 'Hearts', 'Zodiac', 'Symbols', 'Fine Line'], cart_value=1500, image='photo-1516109871644-302377bade6b'),
    dict(name='Small Tattoos (2 to 4 in)', price_label='₹3,500 starting', description='More detail and color for a statement piece.',
         examples=['Butterflies', 'Roses', 'Quotes', 'Anime', 'Floral'], cart_value=3500, image='photo-1643699760676-85e708b52b24'),
    dict(name='Medium Tattoos (4 to 6 in)', price_label='₹7,000 starting', description='Intricate portraits, mandalas and geometric work.',
         examples=['Portraits', 'Animals', 'Mandalas', 'Geometric'], cart_value=7000, image='photo-1564671815737-033b93d141e1'),
    dict(name='Large Tattoos (6 to 10 in)', price_label='₹15,000 starting', description='Bold realism and religious pieces with real presence.',
         examples=['Half Sleeve', 'Religious', 'Realism'], cart_value=15000, image='photo-1513078094721-e7b6e0394a6a'),
    dict(name='XL Tattoos', price_label='Custom Quote', description='Full sleeves and back pieces, priced after consultation.',
         examples=['Full Sleeve', 'Back Piece', 'Leg Sleeve'], cart_value=0, image='photo-1643186167370-5e4011cbe7c8'),
]

OCCASIONS = [
    'Studio appointments', 'Home appointments', 'Birthday events', 'Parties', 'Surprise tattoo gifts',
    'Couple tattoos', 'Friends group bookings', 'Corporate events', 'Private sessions',
]

BOOKING_OPTIONS = [
    dict(icon='User', name='Single Tattoo', description='One-on-one session, fully personalized to your idea and placement.'),
    dict(icon='Users', name='Couple Tattoos', description='Matching or complementary designs booked together, side by side.'),
    dict(icon='UsersRound', name='Friend Group Sessions', description='Bring 3 or more friends and we coordinate one shared appointment slot.'),
    dict(icon='PartyPopper', name='Events', description='On-site tattoo stations for launches, retreats and corporate events.'),
    dict(icon='Sparkles', name='Parties', description='Birthday or celebration parties with flash tattoos for every guest.'),
]

FAQS = [
    ('How do I prepare for my session?', "Sleep well, eat beforehand, stay hydrated and avoid alcohol for 24 hours. We'll cover everything else in your consultation."),
    ('When will I see my design?', "For custom pieces, your artist shares the design before your appointment so we can refine it together."),
    ('Can I bring a companion?', "Of course. One guest is welcome at studio sessions, and home service is happy to include your household."),
    ('How do I care for a new tattoo?', "Keep it clean and moisturized, avoid direct sun and swimming for two weeks. We send a full aftercare guide after booking."),
    ('Do you really offer home service everywhere in India?', "Yes. Law Gate, Phagwara and Jalandhar are free, and every other city has a small transparent travel fee shown at booking."),
    ("I have my own reference, can you use it?", "Absolutely. Upload it during booking and we'll tailor the design and sizing to fit your vision perfectly."),
]


class Command(BaseCommand):
    help = 'Seeds the trimmed, curated studio content: services, a handful of news posts and gallery pieces, one artist, about copy and FAQ.'

    def handle(self, *args, **options):
        # News/Artists/Gallery are cleared first — this command defines the
        # exact curated set, not an ever-growing superset of everything ever added.
        NewsPost.objects.all().delete()
        GalleryItem.objects.all().delete()
        Artist.objects.all().delete()

        artist_by_slug = {}
        for data in ARTISTS:
            obj = Artist.objects.create(**data)
            artist_by_slug[data['slug']] = obj
        self.stdout.write(self.style.SUCCESS(f'Artists: {len(ARTISTS)}'))

        for data in NEWS_POSTS:
            fields = dict(data)
            fields['date'] = datetime.strptime(fields['date'], '%m/%d/%Y').date()
            NewsPost.objects.create(**fields)
        self.stdout.write(self.style.SUCCESS(f'News posts: {len(NEWS_POSTS)}'))

        for category, title, image, artist_slug in GALLERY:
            GalleryItem.objects.create(title=title, category=category, image=image, artist=artist_by_slug[artist_slug])
        self.stdout.write(self.style.SUCCESS(f'Gallery items: {len(GALLERY)}'))

        for i, data in enumerate(SERVICES):
            Service.objects.update_or_create(name=data['name'], defaults={**data, 'order': i})
        self.stdout.write(self.style.SUCCESS(f'Services: {len(SERVICES)}'))

        for i, label in enumerate(OCCASIONS):
            AboutOccasion.objects.update_or_create(label=label, defaults={'order': i})
        self.stdout.write(self.style.SUCCESS(f'About occasions: {len(OCCASIONS)}'))

        for i, data in enumerate(BOOKING_OPTIONS):
            AboutBookingOption.objects.update_or_create(name=data['name'], defaults={**data, 'order': i})
        self.stdout.write(self.style.SUCCESS(f'About booking options: {len(BOOKING_OPTIONS)}'))

        for i, (question, answer) in enumerate(FAQS):
            FAQ.objects.update_or_create(question=question, defaults={'answer': answer, 'order': i})
        self.stdout.write(self.style.SUCCESS(f'FAQs: {len(FAQS)}'))

        self.stdout.write(self.style.SUCCESS('Content seed complete.'))
