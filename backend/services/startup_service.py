import os

from werkzeug.security import generate_password_hash

from extensions import db
from models.activity_log import ActivityLog
from models.booking import Booking, Payment
from models.setting import SystemSetting
from models.ticket import Ticket
from models.user import User
from models.wishlist import WishlistItem
from services.catalog_data import DEFAULT_DISCORD_LINK
from services.catalog_sync_service import (
    apply_featured_movie_details,
    backfill_missing_movie_posters,
    sync_sample_poster_catalog,
    sync_booking_catalog_from_imdbapi,
    sync_booking_catalog_from_tmdb,
    sync_curated_upcoming_catalog,
    sync_theater_network,
)

def create_default_admin():
    admin_email = "nchethan066@gmail.com"
    admin_password = "admin123"
    old_admin_email = "nchethan066@gmai.com"

    old_admin = User.query.filter_by(email=old_admin_email).first()
    if old_admin:
        Ticket.query.filter_by(user_id=old_admin.id).delete()
        old_bookings = Booking.query.filter_by(user_id=old_admin.id).all()

        for booking in old_bookings:
            Payment.query.filter_by(booking_id=booking.id).delete()
            db.session.delete(booking)

        db.session.delete(old_admin)
        db.session.commit()

    existing_admin = User.query.filter_by(email=admin_email).first()

    if existing_admin:
        existing_admin.name = "Admin"
        existing_admin.role = "admin"
        db.session.commit()
    else:
        admin = User(
            name="Admin",
            email=admin_email,
            password=generate_password_hash(admin_password),
            role="admin"
        )

        db.session.add(admin)
        db.session.commit()


def create_default_settings():
    settings = SystemSetting.query.first()

    if not settings:
        settings = SystemSetting()
        db.session.add(settings)
        db.session.commit()
        return

    if not settings.support_discord_link:
        settings.support_discord_link = DEFAULT_DISCORD_LINK
        db.session.commit()


def initialize_app_data():
    db.create_all()

    create_default_settings()
    create_default_admin()
    sync_theater_network()

    if os.environ.get("ENABLE_STARTUP_CATALOG_SYNC", "").lower() in {"1", "true", "yes"}:
        if not sync_booking_catalog_from_tmdb() and not sync_booking_catalog_from_imdbapi():
            sync_curated_upcoming_catalog()

        backfill_missing_movie_posters(limit=12)
    elif not os.environ.get("SKIP_CURATED_CATALOG_SEED", "").lower() in {"1", "true", "yes"}:
        sync_curated_upcoming_catalog()

    sync_sample_poster_catalog()
    apply_featured_movie_details()
