"""Notification endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Notification, User
from backend.schemas import NotificationOut
from backend.routers.auth import require_user

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


@router.get("", response_model=list[NotificationOut])
def list_notifications(user: User = Depends(require_user), db: Session = Depends(get_db)):
    """Get all notifications for the current user."""
    return (
        db.query(Notification)
        .filter(Notification.user_id == user.id)
        .order_by(Notification.created_at.desc())
        .limit(50)
        .all()
    )


@router.get("/unread-count")
def unread_count(user: User = Depends(require_user), db: Session = Depends(get_db)):
    """Get count of unread notifications."""
    count = (
        db.query(Notification)
        .filter(Notification.user_id == user.id, Notification.is_read == False)
        .count()
    )
    return {"count": count}


@router.patch("/{notification_id}/read")
def mark_read(notification_id: str, user: User = Depends(require_user), db: Session = Depends(get_db)):
    """Mark a notification as read."""
    n = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == user.id,
    ).first()
    if not n:
        raise HTTPException(404, "Notification not found")
    n.is_read = True
    db.commit()
    return {"ok": True}


@router.post("/mark-all-read")
def mark_all_read(user: User = Depends(require_user), db: Session = Depends(get_db)):
    """Mark all notifications as read."""
    db.query(Notification).filter(
        Notification.user_id == user.id,
        Notification.is_read == False,
    ).update({"is_read": True})
    db.commit()
    return {"ok": True}


def notify_handlers(db: Session, title: str, message: str, notification_type: str = "info", link: str | None = None):
    """Send a notification to all handlers/admins."""
    from backend.models import UserRole
    handlers = db.query(User).filter(User.role.in_([UserRole.HANDLER, UserRole.ADMIN])).all()
    for h in handlers:
        n = Notification(
            user_id=h.id,
            title=title,
            message=message,
            notification_type=notification_type,
            link=link,
        )
        db.add(n)


def notify_user(db: Session, user_id: str, title: str, message: str, notification_type: str = "info", link: str | None = None):
    """Send a notification to a specific user."""
    n = Notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type,
        link=link,
    )
    db.add(n)
