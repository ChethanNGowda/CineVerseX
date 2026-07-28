"""initial postgresql schema

Revision ID: a1b2c3d4e5f6
Revises: 
Create Date: 2026-07-28 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = "a1b2c3d4e5f6"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=120), nullable=False),
        sa.Column("password", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=True),
        sa.Column("google_id", sa.String(length=120), nullable=True),
        sa.Column("profile_picture", sa.String(length=255), nullable=True),
        sa.Column("email_verified", sa.Boolean(), nullable=True),
        sa.Column("email_verification_token", sa.String(length=120), nullable=True),
        sa.Column("password_reset_token", sa.String(length=120), nullable=True),
        sa.Column("password_reset_expires_at", sa.DateTime(), nullable=True),
        sa.Column("remember_login", sa.Boolean(), nullable=True),
        sa.Column("subscription_plan", sa.String(length=30), nullable=True),
        sa.Column("subscription_status", sa.String(length=30), nullable=True),
        sa.Column("subscription_started_at", sa.DateTime(), nullable=True),
        sa.Column("subscription_expires_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("google_id"),
    )

    op.create_table(
        "movies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("poster_url", sa.String(length=500), nullable=True),
        sa.Column("language", sa.String(length=50), nullable=True),
        sa.Column("genre", sa.String(length=100), nullable=True),
        sa.Column("release_date", sa.String(length=50), nullable=True),
        sa.Column("rating", sa.Float(), nullable=True),
        sa.Column("runtime_minutes", sa.Integer(), nullable=True),
        sa.Column("certificate", sa.String(length=20), nullable=True),
        sa.Column("cast_names", sa.Text(), nullable=True),
        sa.Column("director_names", sa.Text(), nullable=True),
        sa.Column("writer_names", sa.Text(), nullable=True),
        sa.Column("backdrop_url", sa.String(length=500), nullable=True),
        sa.Column("trailer_url", sa.String(length=500), nullable=True),
        sa.Column("justwatch_url", sa.String(length=500), nullable=True),
        sa.Column("bookmyshow_url", sa.String(length=500), nullable=True),
        sa.Column("bookmyshow_movie_url", sa.String(length=500), nullable=True),
        sa.Column("bookmyshow_ticket_url", sa.String(length=500), nullable=True),
        sa.Column("interested_count", sa.Integer(), nullable=True),
        sa.Column("release_status", sa.String(length=50), nullable=True),
        sa.Column("tmdb_id", sa.Integer(), nullable=True),
        sa.Column("tmdb_url", sa.String(length=300), nullable=True),
        sa.Column("data_source", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "theaters",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("city", sa.String(length=100), nullable=False),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("total_screens", sa.Integer(), nullable=True),
        sa.Column("amenities", sa.Text(), nullable=True),
        sa.Column("parking_info", sa.String(length=255), nullable=True),
        sa.Column("food_available", sa.Boolean(), nullable=True),
        sa.Column("map_url", sa.String(length=500), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "system_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("site_name", sa.String(length=100), nullable=True),
        sa.Column("support_email", sa.String(length=120), nullable=True),
        sa.Column("support_discord_link", sa.String(length=255), nullable=True),
        sa.Column("support_phone", sa.String(length=20), nullable=True),
        sa.Column("maintenance_mode", sa.Boolean(), nullable=True),
        sa.Column("booking_enabled", sa.Boolean(), nullable=True),
        sa.Column("registration_enabled", sa.Boolean(), nullable=True),
        sa.Column("max_seats_per_booking", sa.Integer(), nullable=True),
        sa.Column("cancel_hours_before_show", sa.Integer(), nullable=True),
        sa.Column("booking_fee", sa.Float(), nullable=True),
        sa.Column("tax_percentage", sa.Float(), nullable=True),
        sa.Column("payment_gateway_enabled", sa.Boolean(), nullable=True),
        sa.Column("email_notifications_enabled", sa.Boolean(), nullable=True),
        sa.Column("tmdb_last_sync", sa.String(length=20), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "activity_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(length=80), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "screens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("theater_id", sa.Integer(), nullable=True),
        sa.Column("screen_name", sa.String(length=100), nullable=True),
        sa.Column("total_seats", sa.Integer(), nullable=True),
        sa.Column("vip_seats", sa.Integer(), nullable=True),
        sa.Column("premium_seats", sa.Integer(), nullable=True),
        sa.Column("standard_seats", sa.Integer(), nullable=True),
        sa.Column("couple_seats", sa.Integer(), nullable=True),
        sa.Column("wheelchair_seats", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["theater_id"], ["theaters.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "shows",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("movie_id", sa.Integer(), nullable=True),
        sa.Column("theater_id", sa.Integer(), nullable=True),
        sa.Column("screen_id", sa.Integer(), nullable=True),
        sa.Column("show_time", sa.String(length=100), nullable=True),
        sa.Column("price", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["movie_id"], ["movies.id"]),
        sa.ForeignKeyConstraint(["screen_id"], ["screens.id"]),
        sa.ForeignKeyConstraint(["theater_id"], ["theaters.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "bookings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("show_id", sa.Integer(), nullable=True),
        sa.Column("seats", sa.String(length=100), nullable=True),
        sa.Column("total_amount", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=True),
        sa.Column("external_booking_url", sa.String(length=500), nullable=True),
        sa.Column("refund_status", sa.String(length=50), nullable=True),
        sa.Column("refund_reference", sa.String(length=120), nullable=True),
        sa.Column("booked_at", sa.DateTime(), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["show_id"], ["shows.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("booking_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("amount", sa.Float(), nullable=True),
        sa.Column("method", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=True),
        sa.Column("purpose", sa.String(length=50), nullable=True),
        sa.Column("provider_reference", sa.String(length=120), nullable=True),
        sa.Column("receipt_number", sa.String(length=80), nullable=True),
        sa.Column("failure_reason", sa.String(length=255), nullable=True),
        sa.Column("refunded_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["booking_id"], ["bookings.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "tickets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("booking_id", sa.Integer(), nullable=True),
        sa.Column("movie_name", sa.String(length=100), nullable=False),
        sa.Column("theatre_name", sa.String(length=100), nullable=False),
        sa.Column("show_time", sa.String(length=50), nullable=False),
        sa.Column("seat_numbers", sa.String(length=100), nullable=False),
        sa.Column("total_amount", sa.Float(), nullable=False),
        sa.Column("booking_date", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=True),
        sa.Column("qr_code", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(["booking_id"], ["bookings.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "reviews",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("movie_id", sa.Integer(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("likes", sa.Integer(), nullable=True),
        sa.Column("report_count", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["movie_id"], ["movies.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "movie_id", name="unique_user_movie_review"),
    )

    op.create_table(
        "wishlist_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("movie_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["movie_id"], ["movies.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "movie_id", name="uq_wishlist_user_movie"),
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS imdb_image_cache (
            tconst VARCHAR(20) PRIMARY KEY,
            title VARCHAR(300),
            poster_url VARCHAR(600),
            backdrop_url VARCHAR(600),
            source VARCHAR(50),
            updated_at VARCHAR(30)
        )
        """
    )


def downgrade():
    op.drop_table("wishlist_items")
    op.drop_table("reviews")
    op.drop_table("tickets")
    op.drop_table("payments")
    op.drop_table("bookings")
    op.drop_table("shows")
    op.drop_table("screens")
    op.drop_table("activity_logs")
    op.drop_table("system_settings")
    op.drop_table("theaters")
    op.drop_table("movies")
    op.drop_table("users")