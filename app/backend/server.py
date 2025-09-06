from fastapi import FastAPI, APIRouter, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import uuid
import random
import string
import logging

# Local imports
from config import settings
from database import database
from auth import get_current_user, AuthenticatedUser, get_optional_user
from models import *

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await database.connect()
    logger.info("DamnBruh API started successfully")
    yield
    # Shutdown
    await database.disconnect()
    logger.info("DamnBruh API shutdown complete")

# Create the main app
app = FastAPI(
    title="DamnBruh Skill Betting API",
    version="1.0.0",
    description="Backend API for DamnBruh skill-based betting game with Privy integration",
    lifespan=lifespan
)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Utility functions
def generate_referral_code() -> str:
    """Generate a unique referral code"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def calculate_payout(bet_amount: Decimal, rank: int, total_players: int) -> Decimal:
    """Calculate payout based on rank and total players"""
    if rank == 1:
        # Winner gets 1.8x bet amount (minus house edge)
        return bet_amount * Decimal('1.8') * (Decimal('1') - settings.HOUSE_EDGE)
    elif rank <= 3:
        # Top 3 get their bet back
        return bet_amount
    else:
        # Others lose their bet
        return Decimal('0')

# Authentication endpoints
@api_router.post("/auth/verify")
async def verify_auth(user: AuthenticatedUser = Depends(get_current_user)):
    """Verify Privy access token"""
    return {
        "valid": True,
        "user_id": user.user_id,
        "app_id": user.app_id,
        "email": user.email,
        "wallet_address": user.wallet_address
    }

# User management endpoints
@api_router.get("/user/profile", response_model=UserProfile)
async def get_user_profile(user: AuthenticatedUser = Depends(get_current_user)):
    """Get authenticated user's profile"""
    # Get or create user in database
    db_user = await database.get_user_by_privy_id(user.user_id)
    
    if not db_user:
        # Create new user
        referral_code = generate_referral_code()
        
        user_data = {
            "privy_user_id": user.user_id,
            "email": user.email,
            "wallet_address": user.wallet_address,
            "balance": 0.0,
            "total_games": 0,
            "total_winnings": 0.0,
            "referral_code": referral_code,
            "appearance": {
                "color": "#FCD34D",
                "pattern": "solid",
                "accessory": "none"
            }
        }
        
        db_user = await database.create_user(user_data)
        
        # Create affiliate record
        affiliate_data = {
            "user_id": db_user['id'],
            "referral_code": referral_code,
            "commission_rate": float(settings.DEFAULT_COMMISSION_RATE),
            "total_referrals": 0,
            "total_commission": 0.0,
            "pending_commission": 0.0,
            "is_active": True
        }
        await database.create_affiliate(affiliate_data)
    
    return UserProfile(
        user_id=db_user['id'],
        email=db_user.get('email'),
        username=db_user.get('username'),
        display_name=db_user.get('display_name'),
        wallet_address=db_user.get('wallet_address'),
        balance=Decimal(str(db_user.get('balance', 0))),
        total_games=db_user.get('total_games', 0),
        total_winnings=Decimal(str(db_user.get('total_winnings', 0))),
        referral_code=db_user.get('referral_code'),
        referred_by=db_user.get('referred_by'),
        appearance=db_user.get('appearance'),
        created_at=db_user.get('created_at', datetime.utcnow())
    )

@api_router.put("/user/profile")
async def update_user_profile(
    profile_update: UserProfileUpdate,
    user: AuthenticatedUser = Depends(get_current_user)
):
    """Update user profile"""
    db_user = await database.get_user_by_privy_id(user.user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = {}
    if profile_update.username is not None:
        # Check if username is already taken
        existing = await database.db.users.find_one({"username": profile_update.username})
        if existing and existing['_id'] != db_user['id']:
            raise HTTPException(status_code=400, detail="Username already taken")
        update_data['username'] = profile_update.username
    
    if profile_update.display_name is not None:
        update_data['display_name'] = profile_update.display_name
    
    if profile_update.appearance is not None:
        update_data['appearance'] = profile_update.appearance
    
    if update_data:
        await database.update_user(db_user['id'], update_data)
    
    return {"message": "Profile updated successfully"}

@api_router.get("/user/balance", response_model=UserBalance)
async def get_user_balance(user: AuthenticatedUser = Depends(get_current_user)):
    """Get user's current balance"""
    db_user = await database.get_user_by_privy_id(user.user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Calculate pending withdrawals
    pending_withdrawals = await database.db.transactions.aggregate([
        {"$match": {
            "user_id": db_user['id'],
            "type": "withdrawal",
            "status": "pending"
        }},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]).to_list(1)
    
    pending_amount = Decimal(str(pending_withdrawals[0]['total'] if pending_withdrawals else 0))
    
    return UserBalance(
        balance=Decimal(str(db_user.get('balance', 0))),
        currency="SOL",
        wallet_address=db_user.get('wallet_address'),
        pending_withdrawals=pending_amount
    )

# Game endpoints
@api_router.post("/games/join", response_model=GameSession)
async def join_game(
    bet_request: BetRequest,
    user: AuthenticatedUser = Depends(get_current_user)
):
    """Join a game session"""
    db_user = await database.get_user_by_privy_id(user.user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    current_balance = Decimal(str(db_user.get('balance', 0)))
    
    # Check balance
    if current_balance < bet_request.bet_amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
    # Deduct bet amount
    new_balance = current_balance - bet_request.bet_amount
    await database.update_user_balance(db_user['id'], new_balance)
    
    # Create game session
    session_data = {
        "user_id": db_user['id'],
        "game_type": bet_request.game_type,
        "bet_amount": float(bet_request.bet_amount),
        "appearance": bet_request.appearance
    }
    
    game_session = await database.create_game_session(session_data)
    
    # Create transaction record
    transaction_data = {
        "user_id": db_user['id'],
        "type": "bet",
        "amount": float(bet_request.bet_amount),
        "status": "completed",
        "reference_id": game_session['id'],
        "metadata": {"game_type": bet_request.game_type}
    }
    await database.create_transaction(transaction_data)
    
    # Generate mock other players
    other_players = []
    for i in range(random.randint(5, 12)):
        other_players.append({
            "player_id": f"bot_{i}",
            "username": f"Player_{random.randint(1000, 9999)}",
            "score": random.randint(10, 100),
            "appearance": {
                "color": random.choice(["#10B981", "#3B82F6", "#8B5CF6", "#EF4444"]),
                "pattern": "solid",
                "accessory": "none"
            }
        })
    
    return GameSession(
        game_session_id=game_session['id'],
        bet_amount=bet_request.bet_amount,
        new_balance=new_balance,
        game_state="active",
        other_players=other_players
    )

@api_router.post("/games/end", response_model=GameResult)
async def end_game(
    game_end: GameEnd,
    user: AuthenticatedUser = Depends(get_current_user)
):
    """End game session and calculate payouts"""
    db_user = await database.get_user_by_privy_id(user.user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get game session
    session = await database.db.game_sessions.find_one({"_id": game_end.game_session_id})
    if not session or session['user_id'] != db_user['id']:
        raise HTTPException(status_code=404, detail="Game session not found")
    
    # Calculate payout
    bet_amount = Decimal(str(session['bet_amount']))
    total_players = random.randint(8, 15)  # Mock total players
    payout = calculate_payout(bet_amount, game_end.final_rank, total_players)
    
    # Update user balance
    current_balance = Decimal(str(db_user.get('balance', 0)))
    new_balance = current_balance + payout
    await database.update_user_balance(db_user['id'], new_balance)
    
    # Update game session
    session_update = {
        "final_score": game_end.final_score,
        "final_rank": game_end.final_rank,
        "payout": float(payout),
        "status": "completed",
        "ended_at": datetime.utcnow()
    }
    await database.update_game_session(game_end.game_session_id, session_update)
    
    # Update user stats
    user_update = {
        "total_games": db_user.get('total_games', 0) + 1,
        "total_winnings": float(Decimal(str(db_user.get('total_winnings', 0))) + payout)
    }
    await database.update_user(db_user['id'], user_update)
    
    # Create payout transaction if won
    if payout > 0:
        transaction_data = {
            "user_id": db_user['id'],
            "type": "payout",
            "amount": float(payout),
            "status": "completed",
            "reference_id": game_end.game_session_id,
            "metadata": {
                "rank": game_end.final_rank,
                "total_players": total_players,
                "score": game_end.final_score
            }
        }
        await database.create_transaction(transaction_data)
    
    return GameResult(
        payout=payout,
        new_balance=new_balance,
        rank=game_end.final_rank,
        total_players=total_players,
        game_result="win" if game_end.final_rank <= 3 else "loss"
    )

@api_router.get("/games/history", response_model=GameHistory)
async def get_game_history(
    user: AuthenticatedUser = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get user's game history"""
    db_user = await database.get_user_by_privy_id(user.user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    games = await database.get_user_game_history(db_user['id'], limit, offset)
    
    # Get total count
    total = await database.db.game_sessions.count_documents({"user_id": db_user['id']})
    
    # Format games
    formatted_games = []
    for game in games:
        formatted_games.append({
            "game_id": game['id'],
            "game_type": game.get('game_type', 'skill_match'),
            "bet_amount": game.get('bet_amount', 0),
            "payout": game.get('payout', 0),
            "score": game.get('final_score'),
            "rank": game.get('final_rank'),
            "result": "win" if game.get('final_rank', 0) <= 3 else "loss",
            "duration": 0,  # Mock duration
            "timestamp": game.get('created_at')
        })
    
    return GameHistory(
        games=formatted_games,
        total=total,
        has_more=(offset + limit) < total
    )

# Leaderboard endpoints
@api_router.get("/leaderboard/global", response_model=Leaderboard)
async def get_global_leaderboard(
    period: str = Query("all_time", regex="^(daily|weekly|monthly|all_time)$"),
    limit: int = Query(100, ge=1, le=500),
    user: Optional[AuthenticatedUser] = Depends(get_optional_user)
):
    """Get global leaderboard"""
    leaderboard_data = await database.get_global_leaderboard(period, limit)
    
    # Get user's rank if authenticated
    user_rank = None
    if user:
        db_user = await database.get_user_by_privy_id(user.user_id)
        if db_user:
            for entry in leaderboard_data:
                if entry['user_id'] == db_user['id']:
                    user_rank = entry['rank']
                    break
    
    # Format leaderboard
    formatted_leaderboard = []
    for entry in leaderboard_data:
        formatted_leaderboard.append(LeaderboardEntry(
            rank=entry['rank'],
            user_id=entry['user_id'],
            username=entry.get('username', f"Player_{entry['user_id'][:8]}"),
            total_winnings=Decimal(str(entry.get('total_winnings', 0))),
            games_played=entry.get('total_games', 0),
            win_rate=Decimal(str(entry.get('win_rate', 0)))
        ))
    
    return Leaderboard(
        leaderboard=formatted_leaderboard,
        user_rank=user_rank,
        total_players=await database.db.users.count_documents({})
    )

# Include the router in the main app
app.include_router(api_router)

# Root endpoint
@app.get("/")
async def root():
    return {"message": "DamnBruh API is running!", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)