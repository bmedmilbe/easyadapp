# core/middleware.py
from django.utils import timezone

from .models import SessionManager


class EasyFlowMiddleware:
    """Middleware to handle anonymous sessions for easyflow"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Get or create session key
        session_key = request.COOKIES.get('easyflow_session')
        
        if not session_key:
            import uuid
            session_key = str(uuid.uuid4())
            request.easyflow_session = None
        else:
            try:
                session = SessionManager.objects.get(
                    session_key=session_key,
                    expires_at__gt=timezone.now()
                )
                request.easyflow_session = session
            except SessionManager.DoesNotExist:
                request.easyflow_session = None
        
        request.easyflow_session_key = session_key
        
        response = self.get_response(request)
        
        # Set cookie if not exists
        if not request.COOKIES.get('easyflow_session'):
            import uuid
            new_session_key = str(uuid.uuid4())
            response.set_cookie(
                'easyflow_session',
                new_session_key,
                max_age=60*60*24*30,  # 30 days
                httponly=True,
                secure=True,
                samesite='Lax'
            )
        
        return response