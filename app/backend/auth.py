from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from privy_client import privy_client
from typing import Optional
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()

class AuthenticatedUser:
    def __init__(self, user_id: str, app_id: str, email: Optional[str] = None, wallet_address: Optional[str] = None):
        self.user_id = user_id
        self.app_id = app_id
        self.email = email
        self.wallet_address = wallet_address

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> AuthenticatedUser:
    """
    Dependency to verify Privy access token and return authenticated user
    """
    token = credentials.credentials
    
    # Verify token with Privy
    verified_claims = await privy_client.verify_token(token)
    
    if not verified_claims:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract user information from claims
    user_id = verified_claims.get('sub')  # Subject is the user ID
    app_id = verified_claims.get('aud')   # Audience is the app ID
    
    if not user_id or not app_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token claims",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get additional user info from Privy API
    user_info = await privy_client.get_user(token)
    email = None
    wallet_address = None
    
    if user_info:
        # Extract email
        email_obj = user_info.get('email')
        if email_obj:
            email = email_obj.get('address')
        
        # Extract wallet address (embedded wallet)
        wallets = user_info.get('linkedAccounts', [])
        for wallet in wallets:
            if wallet.get('type') == 'wallet':
                wallet_address = wallet.get('address')
                break
    
    return AuthenticatedUser(
        user_id=user_id,
        app_id=app_id,
        email=email,
        wallet_address=wallet_address
    )

async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[AuthenticatedUser]:
    """
    Optional authentication dependency for endpoints that work with or without auth
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None