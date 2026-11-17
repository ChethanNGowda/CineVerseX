import os
import qrcode
from datetime import datetime
from uuid import uuid4

from flask import (
    Blueprint,
    flash,
    render_template,
    request,
    session,
    redirect,
    url_for,
    current_app
)

from extensions import db
from auth.guards import login_required
from models.show import Show
from models.booking import Booking, Payment
from models.setting import SystemSetting
from models.ticket import Ticket
from models.user import User
from services.activity_service import log_activity
from services.catalog_data import BOOKMYSHOW_HOME_URL
from services.catalog_sync_service import bookmyshow_search_url
from services.email_service import send_ticket_email

booking_bp = Blueprint("booking_bp", __name__)

ACTIVE_BOOKING_STATUSES = ("Booked", "confirmed")


def get_settings():
    settings = SystemSetting.query.first()

    if not settings:
        settings = SystemSetting()
        db.session.add(settings)
        db.session.commit()

    return settings


def parse_show_time(show_time):
    if not show_time:
        return None

    formats = (
        "%Y-%m-%d %H:%M",
        "%Y-%m-%dT%H:%M",
        "%d-%m-%Y %H:%M",
        "%d/%m/%Y %H:%M",
        "%Y-%m-%d %I:%M %p",
        "%d-%m-%Y %I:%M %p",
        "%I:%M %p",
    )

    for date_format in formats:
        try:
            return datetime.strptime(show_time, date_format)
        except ValueError:
            continue

    return None


def effective_bookmyshow_url(movie):
    if not movie:
        return BOOKMYSHOW_HOME_URL

    return movie.bookmyshow_url or bookmyshow_search_url(movie.title)


def seat_label(prefix, count):
    return [f"{prefix}{number}" for number in range(1, max(count, 0) + 1)]


def screen_seats(screen):
    total = screen.total_seats if screen else 80
    vip = screen.vip_seats or max(total // 10, 4)
    premium = screen.premium_seats or max(total // 4, 12)
    couple = screen.couple_seats or max(total // 20, 2)
    wheelchair = screen.wheelchair_seats or 2
    standard = screen.standard_seats or max(total - vip - premium - couple - wheelchair, 0)

    return {
        "VIP": seat_label("V", vip),
        "Premium": seat_label("P", premium),
        "Standard": seat_label("S", standard),
        "Couple": seat_label("C", couple),
        "Wheelchair": seat_label("W", wheelchair),
    }


def seat_price(base_price, seat):
    base = float(base_price or 0)
    multipliers = {
        "V": 1.8,
        "P": 1.35,
        "C": 2.0,
        "W": 1.0,
        "S": 1.0,
    }
    return round(base * multipliers.get(seat[:1], 1.0), 2)


@booking_bp.route("/show/<int:show_id>/seats")
def seat_selection(show_id):
    """Send customers to the cinema ticketing provider instead of fake seat inventory."""
    show = Show.query.get_or_404(show_id)
    return redirect(effective_bookmyshow_url(show.movie))


@booking_bp.route("/book/<int:show_id>", methods=["POST"])
def book_ticket(show_id):
    """Legacy booking endpoint: never create an unverified local payment or ticket."""
    show = Show.query.get_or_404(show_id)
    return redirect(effective_bookmyshow_url(show.movie))


@booking_bp.route("/cancel-ticket/<int:booking_id>", methods=["POST"])
@login_required
def cancel_ticket(booking_id):
    settings = get_settings()
    booking = Booking.query.get_or_404(booking_id)

    if booking.user_id != session["user_id"] and session.get("user_role") != "admin":
        flash("You are not allowed to cancel this ticket.", "danger")
        return redirect(url_for("ticket_bp.my_tickets"))

    if booking.status == "Cancelled":
        flash("Ticket is already cancelled.", "warning")
        return redirect(url_for("ticket_bp.my_tickets"))

    show_time = parse_show_time(booking.show.show_time if booking.show else None)
    if show_time:
        hours_until_show = (show_time - datetime.utcnow()).total_seconds() / 3600

        if hours_until_show < settings.cancel_hours_before_show:
            flash(
                f"Tickets can only be cancelled at least {settings.cancel_hours_before_show} hours before show time.",
                "danger"
            )
            return redirect(url_for("ticket_bp.my_tickets"))

    booking.status = "Cancelled"
    booking.refund_status = "Pending" if float(booking.total_amount or 0) > 0 else "Not Required"
    booking.refund_reference = f"refund_{uuid4().hex[:12]}" if booking.refund_status == "Pending" else ""
    booking.cancelled_at = datetime.utcnow()

    ticket = Ticket.query.filter_by(booking_id=booking.id).first()
    if ticket:
        ticket.status = "Cancelled"

    payment = Payment.query.filter_by(booking_id=booking.id).first()
    if payment and payment.status == "success":
        payment.status = "refunded"
        payment.refunded_at = datetime.utcnow()

    db.session.commit()
    log_activity("Ticket Cancelled", f"Booking #{booking.id} cancelled.", notify=True)

    flash("Ticket cancelled successfully. Refund status has been updated.", "success")
    return redirect(url_for("ticket_bp.my_tickets"))


@booking_bp.route("/bookings")
@login_required
def bookings():
    user_bookings = Booking.query.filter_by(
        user_id=session["user_id"]
    ).all()

    return render_template(
        "bookings.html",
        bookings=user_bookings
    )


@booking_bp.route("/ticket/<int:booking_id>")
@login_required
def ticket_details(booking_id):
    booking = Booking.query.get_or_404(booking_id)

    if booking.user_id != session["user_id"] and session.get("user_role") != "admin":
        return "Access denied", 403

    return render_template(
        "ticket_details.html",
        booking=booking
    )


@booking_bp.route("/booking-history")
@login_required
def booking_history():
    if session.get("user_role") == "admin":
        bookings = Booking.query.order_by(Booking.booked_at.desc()).all()
    else:
        bookings = Booking.query.filter_by(user_id=session["user_id"])\
            .order_by(Booking.booked_at.desc()).all()

    return render_template("booking_history.html", bookings=bookings)
