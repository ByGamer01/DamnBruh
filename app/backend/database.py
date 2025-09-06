from motor.motor_asyncio import AsyncIOMotorClient
from config import settings
from typing import Optional, Dict, Any, List
from decimal import Decimal
from datetime import datetime, timedelta
import uuid
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
    
    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(settings.MONGO_URL)
            self.db = self.client[settings.DB_NAME]
            
            # Test connection
            await self.client.admin.command('ping')
            logger.info("Connected to MongoDB successfully")
            
            # Create indexes
            await self._create_indexes()
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")
    
    async def _create_indexes(self):
        """Create necessary database indexes"""
        try:
            # Users indexes
            await self.db.users.create_index("privy_user_id", unique=True)
            await self.db.users.create_index("username", unique=True, sparse=True)
            await self.db.users.create_index("referral_code", unique=True, sparse=True)
            
            # Game sessions indexes
            await self.db.game_sessions.create_index([("user_id", 1), ("created_at", -1)])
            await self.db.game_sessions.create_index("status")
            
            # Transactions indexes
            await self.db.transactions.create_index([("user_id", 1), ("created_at", -1)])
            await self.db.transactions.create_index("status")
            await self.db.transactions.create_index("type")
            
            # Affiliates indexes
            await self.db.affiliates.create_index("user_id", unique=True)
            await self.db.affiliates.create_index("referral_code", unique=True)
            
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
    
    # User operations
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user"""
        user_data['_id'] = str(uuid.uuid4())
        user_data['created_at'] = datetime.utcnow()
        user_data['updated_at'] = datetime.utcnow()
        
        result = await self.db.users.insert_one(user_data)
        user_data['id'] = user_data['_id']
        return user_data
    
    async def get_user_by_privy_id(self, privy_user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by Privy user ID"""
        user = await self.db.users.find_one({"privy_user_id": privy_user_id})
        if user:
            user['id'] = user['_id']
        return user
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        user = await self.db.users.find_one({"_id": user_id})
        if user:
            user['id'] = user['_id']
        return user
    
    async def update_user(self, user_id: str, update_data: Dict[str, Any]) -> bool:
        """Update user data"""
        update_data['updated_at'] = datetime.utcnow()
        result = await self.db.users.update_one(
            {"_id": user_id},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    async def update_user_balance(self, user_id: str, new_balance: Decimal) -> bool:
        """Update user balance"""
        result = await self.db.users.update_one(
            {"_id": user_id},
            {"$set": {"balance": float(new_balance), "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0
    
    # Game operations
    async def create_game_session(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new game session"""
        session_data['_id'] = str(uuid.uuid4())
        session_data['created_at'] = datetime.utcnow()
        session_data['status'] = 'active'
        
        await self.db.game_sessions.insert_one(session_data)
        session_data['id'] = session_data['_id']
        return session_data
    
    async def update_game_session(self, session_id: str, update_data: Dict[str, Any]) -> bool:
        """Update game session"""
        result = await self.db.game_sessions.update_one(
            {"_id": session_id},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    async def get_user_game_history(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Get user's game history"""
        cursor = self.db.game_sessions.find(
            {"user_id": user_id}
        ).sort("created_at", -1).skip(offset).limit(limit)
        
        games = []
        async for game in cursor:
            game['id'] = game['_id']
            games.append(game)
        
        return games
    
    # Transaction operations
    async def create_transaction(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new transaction"""
        transaction_data['_id'] = str(uuid.uuid4())
        transaction_data['created_at'] = datetime.utcnow()
        transaction_data['status'] = transaction_data.get('status', 'pending')
        
        await self.db.transactions.insert_one(transaction_data)
        transaction_data['id'] = transaction_data['_id']
        return transaction_data
    
    async def update_transaction(self, transaction_id: str, update_data: Dict[str, Any]) -> bool:
        """Update transaction"""
        result = await self.db.transactions.update_one(
            {"_id": transaction_id},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    async def get_user_transactions(self, user_id: str, transaction_type: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user's transactions"""
        query = {"user_id": user_id}
        if transaction_type:
            query["type"] = transaction_type
        
        cursor = self.db.transactions.find(query).sort("created_at", -1).limit(limit)
        
        transactions = []
        async for txn in cursor:
            txn['id'] = txn['_id']
            transactions.append(txn)
        
        return transactions
    
    # Leaderboard operations
    async def get_global_leaderboard(self, period: str = "all_time", limit: int = 100) -> List[Dict[str, Any]]:
        """Get global leaderboard"""
        # Calculate date filter based on period
        date_filter = {}
        if period == "daily":
            date_filter = {"created_at": {"$gte": datetime.utcnow() - timedelta(days=1)}}
        elif period == "weekly":
            date_filter = {"created_at": {"$gte": datetime.utcnow() - timedelta(days=7)}}
        elif period == "monthly":
            date_filter = {"created_at": {"$gte": datetime.utcnow() - timedelta(days=30)}}
        
        pipeline = [
            {"$match": date_filter} if date_filter else {"$match": {}},
            {"$sort": {"total_winnings": -1, "total_games": -1}},
            {"$limit": limit},
            {"$project": {
                "user_id": "$_id",
                "username": 1,
                "total_winnings": 1,
                "total_games": 1,
                "win_rate": {"$cond": [
                    {"$eq": ["$total_games", 0]},
                    0,
                    {"$divide": ["$total_wins", "$total_games"]}
                ]}
            }}
        ]
        
        leaderboard = []
        async for user in self.db.users.aggregate(pipeline):
            leaderboard.append(user)
        
        # Add ranks
        for i, user in enumerate(leaderboard):
            user['rank'] = i + 1
        
        return leaderboard
    
    # Affiliate operations
    async def create_affiliate(self, affiliate_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create affiliate record"""
        affiliate_data['_id'] = str(uuid.uuid4())
        affiliate_data['created_at'] = datetime.utcnow()
        
        await self.db.affiliates.insert_one(affiliate_data)
        affiliate_data['id'] = affiliate_data['_id']
        return affiliate_data
    
    async def get_affiliate_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get affiliate by user ID"""
        affiliate = await self.db.affiliates.find_one({"user_id": user_id})
        if affiliate:
            affiliate['id'] = affiliate['_id']
        return affiliate
    
    async def get_affiliate_by_code(self, referral_code: str) -> Optional[Dict[str, Any]]:
        """Get affiliate by referral code"""
        affiliate = await self.db.affiliates.find_one({"referral_code": referral_code})
        if affiliate:
            affiliate['id'] = affiliate['_id']
        return affiliate

# Global database instance
database = Database()