from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from decimal import Decimal
from datetime import datetime
import re

# Request Models
class BetRequest(BaseModel):
    bet_amount: Decimal = Field(..., gt=0, max_digits=18, decimal_places=6)
    game_type: str = Field(..., min_length=1, max_length=32)
    appearance: Optional[Dict[str, Any]] = None
    
    @validator('bet_amount')
    def validate_bet_amount(cls, v):
        if v <= 0:
            raise ValueError('Bet amount must be positive')
        if v > Decimal('10.0'):  # Maximum bet limit
            raise ValueError('Bet amount exceeds maximum limit')
        return v
    
    @validator('game_type')
    def validate_game_type(cls, v):
        allowed_types = ['skill_match', 'tournament', 'practice']
        if v not in allowed_types:
            raise ValueError(f'Game type must be one of: {allowed_types}')
        return v

class WithdrawalRequest(BaseModel):
    amount: Decimal = Field(..., gt=0, max_digits=18, decimal_places=6)
    destination_address: str = Field(..., min_length=40, max_length=50)
    token_type: str = Field(default="SOL")
    
    @validator('destination_address')
    def validate_address(cls, v):
        # Basic Ethereum/Solana address validation
        if not (re.match(r'^0x[a-fA-F0-9]{40}$', v) or re.match(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$', v)):
            raise ValueError('Invalid wallet address format')
        return v.lower() if v.startswith('0x') else v
    
    @validator('amount')
    def validate_withdrawal_amount(cls, v):
        min_withdrawal = Decimal('0.01')
        max_withdrawal = Decimal('100.0')
        
        if v < min_withdrawal:
            raise ValueError(f'Minimum withdrawal amount is {min_withdrawal}')
        if v > max_withdrawal:
            raise ValueError(f'Maximum withdrawal amount is {max_withdrawal}')
        return v

class UserProfileUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=20)
    display_name: Optional[str] = Field(None, min_length=1, max_length=50)
    appearance: Optional[Dict[str, Any]] = None
    
    @validator('username')
    def validate_username(cls, v):
        if v is None:
            return v
        
        # Username can only contain alphanumeric characters and underscores
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username can only contain letters, numbers, and underscores')
        
        # Check for prohibited usernames
        prohibited = ['admin', 'system', 'support', 'moderator', 'damnbruh']
        if v.lower() in prohibited:
            raise ValueError('Username not allowed')
        
        return v

class ScoreUpdate(BaseModel):
    game_session_id: str
    score: int = Field(..., ge=0)
    game_events: Optional[List[Dict[str, Any]]] = None

class GameEnd(BaseModel):
    game_session_id: str
    final_score: int = Field(..., ge=0)
    final_rank: int = Field(..., ge=1)

class FriendRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=20)

class FriendAccept(BaseModel):
    user_id: str = Field(..., min_length=1)

class CommissionWithdrawal(BaseModel):
    amount: Decimal = Field(..., gt=0, max_digits=18, decimal_places=6)
    destination_address: str = Field(..., min_length=40, max_length=50)

# Response Models
class UserProfile(BaseModel):
    user_id: str
    email: Optional[str]
    username: Optional[str]
    display_name: Optional[str]
    wallet_address: Optional[str]
    balance: Decimal
    total_games: int
    total_winnings: Decimal
    referral_code: Optional[str]
    referred_by: Optional[str]
    appearance: Optional[Dict[str, Any]]
    created_at: datetime

class UserBalance(BaseModel):
    balance: Decimal
    currency: str = "SOL"
    wallet_address: Optional[str]
    pending_withdrawals: Decimal = Decimal('0')

class GameSession(BaseModel):
    game_session_id: str
    bet_amount: Decimal
    new_balance: Decimal
    game_state: str
    other_players: List[Dict[str, Any]] = []

class GameResult(BaseModel):
    payout: Decimal
    new_balance: Decimal
    rank: int
    total_players: int
    game_result: str

class GameHistory(BaseModel):
    games: List[Dict[str, Any]]
    total: int
    has_more: bool

class LeaderboardEntry(BaseModel):
    rank: int
    user_id: str
    username: Optional[str]
    total_winnings: Decimal
    games_played: int
    win_rate: Decimal

class Leaderboard(BaseModel):
    leaderboard: List[LeaderboardEntry]
    user_rank: Optional[int]
    total_players: int

class WithdrawalResponse(BaseModel):
    withdrawal_id: str
    status: str
    amount: Decimal
    fee: Decimal = Decimal('0')
    estimated_completion: Optional[datetime]
    new_balance: Decimal

class TransactionHistory(BaseModel):
    transactions: List[Dict[str, Any]]
    total: int

class AffiliateStats(BaseModel):
    referral_code: str
    total_referrals: int
    active_referrals: int
    total_commission: Decimal
    pending_commission: Decimal
    commission_rate: Decimal
    referral_stats: Dict[str, Any] = {}

class FriendsList(BaseModel):
    friends: List[Dict[str, Any]]
    pending_requests: List[Dict[str, Any]]