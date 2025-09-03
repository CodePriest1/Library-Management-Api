from ..models import AuditLog

def log_action(user, action, details=""):
    AuditLog.objects.create(
        user=user if user.is_authenticated else None,
        action=action,
        details=details,
    )


