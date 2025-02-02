from celery import shared_task
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.accounts.models import ActivationTokenModel
from core.database import SessionLocal

logger = logging.getLogger(__name__)


@shared_task
def check_expired_activation_tokens():
    """
     Check expired activation tokens
     and delete them
    """
    logger.info("Task check_expired_activation_tokens started")
    now = datetime.now(timezone.utc)

    db: Session = SessionLocal()

    try:
        expired_tokens = db.query(ActivationTokenModel).filter(
            ActivationTokenModel.expires_at < now
        ).all()

        if expired_tokens:
            for token in expired_tokens:
                db.delete(token)
            db.commit()

        else:
            logger.info("No expired tokens found.")

    except Exception as e:
        db.rollback()
        logger.error(f"Error while checking expired activation tokens: {str(e)}")
        return {"error": str(e)}

    finally:
        db.close()
