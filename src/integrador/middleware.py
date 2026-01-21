# -*- coding: utf-8 -*-
import re
import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class DisableCSRFForAPIMiddleware(MiddlewareMixin):
    """
    Middleware to disable CSRF checking for specific API endpoints.
    """
    
    # Padrões de URL que devem ser isentos de CSRF
    CSRF_EXEMPT_URLS = [
        re.compile(r'^api/enviar_diarios/'),
        re.compile(r'^api/baixar_notas/'),
    ]
    
    def process_request(self, request):
        """
        Marca a requisição como isenta de CSRF se a URL corresponder aos padrões.
        """
        path = request.path_info.lstrip('/')
        logger.info(f"DisableCSRFForAPIMiddleware checking path: {path}")
        
        for pattern in self.CSRF_EXEMPT_URLS:
            if pattern.match(path):
                logger.info(f"CSRF exemption applied for path: {path}")
                setattr(request, '_dont_enforce_csrf_checks', True)
                break
        
        return None
