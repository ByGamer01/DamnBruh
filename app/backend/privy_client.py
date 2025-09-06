import requests
from jose import jwt, JWTError
from config import settings
import logging
from typing import Optional, Dict, Any
import time

logger = logging.getLogger(__name__)

class PrivyClient:
    def __init__(self):
        self.app_id = settings.PRIVY_APP_ID
        self.app_secret = settings.PRIVY_APP_SECRET
        self.base_url = "https://auth.privy.io"
        
        # Cache for JWKs
        self._jwks_cache = None
        self._jwks_cache_time = 0
        self._jwks_cache_ttl = 3600  # 1 hour
    
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify Privy access token and return user claims
        """
        try:
            # Get JWKs for verification
            jwks = await self._get_jwks()
            
            # Decode token header to get key ID
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get('kid')
            
            # Find the matching key
            key = None
            for jwk in jwks.get('keys', []):
                if jwk.get('kid') == kid:
                    key = jwk
                    break
            
            if not key:
                logger.error("No matching key found for token")
                return None
            
            # Verify and decode token
            claims = jwt.decode(
                token,
                key,
                algorithms=['RS256'],
                audience=self.app_id,
                issuer=f"{self.base_url}"
            )
            
            return claims
            
        except JWTError as e:
            logger.error(f"JWT verification failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return None
    
    async def _get_jwks(self) -> Dict[str, Any]:
        """Get JWKs for token verification with caching"""
        current_time = time.time()
        
        # Return cached JWKs if still valid
        if (self._jwks_cache and 
            current_time - self._jwks_cache_time < self._jwks_cache_ttl):
            return self._jwks_cache
        
        try:
            response = requests.get(
                f"{self.base_url}/.well-known/jwks.json",
                timeout=10
            )
            response.raise_for_status()
            
            jwks = response.json()
            
            # Update cache
            self._jwks_cache = jwks
            self._jwks_cache_time = current_time
            
            return jwks
            
        except Exception as e:
            logger.error(f"Failed to fetch JWKs: {e}")
            # Return cached JWKs if available, even if expired
            if self._jwks_cache:
                return self._jwks_cache
            raise
    
    async def get_user(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Get user information from Privy API
        """
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'privy-app-id': self.app_id
            }
            
            response = requests.get(
                f"{self.base_url}/api/v1/users/me",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get user info: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching user info: {e}")
            return None

# Global Privy client instance
privy_client = PrivyClient()