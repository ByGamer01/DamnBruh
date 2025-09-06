# DamnBruh API Contracts & Integration Plan

## Overview
Complete contracts for DamnBruh skill-based betting game with Privy integration, crypto wallets, and affiliate system.

## Authentication & Wallet Integration

### Privy Integration Requirements
- **Frontend**: `@privy-io/react-auth` for auth and embedded wallets
- **Backend**: `privy-client` for token verification
- **Supported Wallets**: Embedded wallets, MetaMask, WalletConnect
- **Blockchain**: Ethereum mainnet with SOL token support

### Required Environment Variables
```bash
# Frontend (.env)
REACT_APP_PRIVY_APP_ID=your_privy_app_id
REACT_APP_BACKEND_URL=existing_backend_url

# Backend (.env)
PRIVY_APP_ID=your_privy_app_id
PRIVY_APP_SECRET=your_privy_app_secret
PRIVY_VERIFICATION_KEY=your_verification_key
```

## API Endpoints Specification

### Authentication Endpoints

#### POST /api/auth/verify
**Purpose**: Verify Privy access token
**Headers**: `Authorization: Bearer <token>`
**Response**:
```json
{
  "valid": true,
  "user_id": "string",
  "app_id": "string"
}
```

### User Management Endpoints

#### GET /api/user/profile
**Purpose**: Get authenticated user profile
**Headers**: `Authorization: Bearer <token>`
**Response**:
```json
{
  "user_id": "string",
  "email": "string",
  "username": "string",
  "wallet_address": "string",
  "balance": "decimal",
  "created_at": "datetime",
  "total_games": "integer",
  "total_winnings": "decimal",
  "referral_code": "string",
  "referred_by": "string|null"
}
```

#### PUT /api/user/profile
**Purpose**: Update user profile
**Body**:
```json
{
  "username": "string",
  "display_name": "string"
}
```

#### GET /api/user/balance
**Purpose**: Get user wallet balance
**Response**:
```json
{
  "balance": "decimal",
  "currency": "SOL",
  "wallet_address": "string",
  "pending_withdrawals": "decimal"
}
```

### Game Endpoints

#### POST /api/games/join
**Purpose**: Join a game session
**Body**:
```json
{
  "bet_amount": "decimal",
  "game_type": "skill_match|tournament|practice",
  "appearance": {
    "color": "string",
    "pattern": "string",
    "accessory": "string"
  }
}
```
**Response**:
```json
{
  "game_session_id": "string",
  "bet_amount": "decimal",
  "new_balance": "decimal",
  "game_state": "active",
  "other_players": [
    {
      "player_id": "string",
      "username": "string",
      "score": "integer",
      "appearance": "object"
    }
  ]
}
```

#### POST /api/games/score-update
**Purpose**: Update player score during game
**Body**:
```json
{
  "game_session_id": "string",
  "score": "integer",
  "game_events": [
    {
      "type": "food_collected|player_killed|death",
      "points": "integer",
      "timestamp": "datetime"
    }
  ]
}
```

#### POST /api/games/end
**Purpose**: End game session and calculate payouts
**Body**:
```json
{
  "game_session_id": "string",
  "final_score": "integer",
  "final_rank": "integer"
}
```
**Response**:
```json
{
  "payout": "decimal",
  "new_balance": "decimal",
  "rank": "integer",
  "total_players": "integer",
  "game_result": "win|loss"
}
```

#### GET /api/games/history
**Purpose**: Get user's game history
**Query**: `?limit=50&offset=0`
**Response**:
```json
{
  "games": [
    {
      "game_id": "string",
      "game_type": "string",
      "bet_amount": "decimal",
      "payout": "decimal",
      "score": "integer",
      "rank": "integer",
      "result": "win|loss",
      "duration": "integer",
      "timestamp": "datetime"
    }
  ],
  "total": "integer",
  "has_more": "boolean"
}
```

### Leaderboard Endpoints

#### GET /api/leaderboard/global
**Purpose**: Get global leaderboard
**Query**: `?period=daily|weekly|monthly|all_time&limit=100`
**Response**:
```json
{
  "leaderboard": [
    {
      "rank": "integer",
      "user_id": "string",
      "username": "string",
      "total_winnings": "decimal",
      "games_played": "integer",
      "win_rate": "decimal"
    }
  ],
  "user_rank": "integer|null",
  "total_players": "integer"
}
```

### Wallet & Transaction Endpoints

#### POST /api/wallet/deposit
**Purpose**: Record crypto deposit (webhook from blockchain)
**Body**:
```json
{
  "user_id": "string",
  "amount": "decimal",
  "transaction_hash": "string",
  "block_number": "integer",
  "token_type": "SOL|ETH|USDT"
}
```

#### POST /api/wallet/withdraw
**Purpose**: Initiate withdrawal
**Body**:
```json
{
  "amount": "decimal",
  "destination_address": "string",
  "token_type": "SOL"
}
```
**Response**:
```json
{
  "withdrawal_id": "string",
  "status": "pending",
  "amount": "decimal",
  "fee": "decimal",
  "estimated_completion": "datetime",
  "new_balance": "decimal"
}
```

#### GET /api/wallet/withdrawals
**Purpose**: Get withdrawal history
**Response**:
```json
{
  "withdrawals": [
    {
      "withdrawal_id": "string",
      "amount": "decimal",
      "fee": "decimal",
      "status": "pending|completed|failed",
      "destination_address": "string",
      "transaction_hash": "string|null",
      "created_at": "datetime",
      "completed_at": "datetime|null"
    }
  ]
}
```

### Affiliate System Endpoints

#### GET /api/affiliates/dashboard
**Purpose**: Get affiliate dashboard data
**Response**:
```json
{
  "referral_code": "string",
  "total_referrals": "integer",
  "active_referrals": "integer",
  "total_commission": "decimal",
  "pending_commission": "decimal",
  "commission_rate": "decimal",
  "referral_stats": {
    "this_month": {
      "referrals": "integer",
      "commission": "decimal"
    },
    "last_month": {
      "referrals": "integer",
      "commission": "decimal"
    }
  }
}
```

#### GET /api/affiliates/referrals
**Purpose**: Get detailed referral list
**Response**:
```json
{
  "referrals": [
    {
      "user_id": "string",
      "username": "string",
      "joined_at": "datetime",
      "total_bets": "decimal",
      "commission_earned": "decimal",
      "is_active": "boolean",
      "last_activity": "datetime"
    }
  ]
}
```

#### POST /api/affiliates/withdraw-commission
**Purpose**: Withdraw affiliate commission
**Body**:
```json
{
  "amount": "decimal",
  "destination_address": "string"
}
```

### Friends System Endpoints

#### GET /api/friends
**Purpose**: Get user's friends list
**Response**:
```json
{
  "friends": [
    {
      "user_id": "string",
      "username": "string",
      "is_online": "boolean",
      "is_playing": "boolean",
      "last_seen": "datetime"
    }
  ],
  "pending_requests": [
    {
      "user_id": "string",
      "username": "string",
      "requested_at": "datetime"
    }
  ]
}
```

#### POST /api/friends/add
**Purpose**: Send friend request
**Body**:
```json
{
  "username": "string"
}
```

#### POST /api/friends/accept
**Purpose**: Accept friend request
**Body**:
```json
{
  "user_id": "string"
}
```

## Database Models

### Users Table
```sql
CREATE TABLE users (
  id VARCHAR(255) PRIMARY KEY,
  privy_user_id VARCHAR(255) UNIQUE NOT NULL,
  email VARCHAR(255),
  username VARCHAR(50) UNIQUE,
  display_name VARCHAR(100),
  wallet_address VARCHAR(42),
  balance DECIMAL(18,6) DEFAULT 0,
  total_games INTEGER DEFAULT 0,
  total_winnings DECIMAL(18,6) DEFAULT 0,
  referral_code VARCHAR(20) UNIQUE,
  referred_by VARCHAR(255),
  appearance JSON,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### Game Sessions Table
```sql
CREATE TABLE game_sessions (
  id VARCHAR(255) PRIMARY KEY,
  user_id VARCHAR(255) NOT NULL,
  game_type VARCHAR(50) NOT NULL,
  bet_amount DECIMAL(18,6) NOT NULL,
  final_score INTEGER,
  final_rank INTEGER,
  payout DECIMAL(18,6) DEFAULT 0,
  status VARCHAR(20) DEFAULT 'active',
  started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  ended_at TIMESTAMP NULL,
  FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### Transactions Table
```sql
CREATE TABLE transactions (
  id VARCHAR(255) PRIMARY KEY,
  user_id VARCHAR(255) NOT NULL,
  type VARCHAR(50) NOT NULL, -- 'deposit', 'withdrawal', 'bet', 'payout', 'commission'
  amount DECIMAL(18,6) NOT NULL,
  status VARCHAR(20) DEFAULT 'pending',
  reference_id VARCHAR(255), -- game_session_id, withdrawal_id, etc.
  transaction_hash VARCHAR(255),
  metadata JSON,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  completed_at TIMESTAMP NULL,
  FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### Affiliates Table
```sql
CREATE TABLE affiliates (
  id VARCHAR(255) PRIMARY KEY,
  user_id VARCHAR(255) NOT NULL,
  referral_code VARCHAR(20) UNIQUE NOT NULL,
  commission_rate DECIMAL(5,4) DEFAULT 0.05, -- 5%
  total_referrals INTEGER DEFAULT 0,
  total_commission DECIMAL(18,6) DEFAULT 0,
  pending_commission DECIMAL(18,6) DEFAULT 0,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id)
);
```

## Frontend Integration Points

### Mock Data to Replace
1. **mockLeaderboard** → Replace with `/api/leaderboard/global`
2. **mockGameStats** → Replace with real-time game data
3. **mockUserData** → Replace with `/api/user/profile`
4. **mockFriends** → Replace with `/api/friends`

### Component Updates Required
1. **AuthComponent** → Integrate Privy authentication
2. **WalletComponent** → Connect to Privy embedded wallets
3. **GameCenter** → Connect to real game API
4. **Leaderboard** → Fetch real leaderboard data
5. **AppearanceCustomizer** → Save to backend

### New Components to Create
1. **AffiliatesDashboard** → Manage referrals and commissions
2. **TransactionHistory** → Show deposits/withdrawals
3. **FriendsManager** → Handle friend invitations
4. **WithdrawalModal** → Process crypto withdrawals

## Security Considerations

### Rate Limiting
- **Betting**: 10 bets per minute per user
- **Withdrawals**: 3 withdrawal requests per minute
- **API calls**: 60 requests per minute per user

### Input Validation
- All monetary amounts validated with proper decimal precision
- Ethereum addresses validated with regex
- Username/display name sanitized against XSS
- Game data validated for tampering

### Financial Security
- All transactions use idempotency keys
- Double-entry bookkeeping for balance tracking
- Comprehensive audit logging
- Withdrawal limits enforced

## Implementation Priority

### Phase 1: Core Backend
1. User authentication with Privy
2. Basic game API
3. Wallet integration
4. Simple leaderboard

### Phase 2: Advanced Features
1. Friends system
2. Affiliate system
3. Advanced game mechanics
4. Real-time updates

### Phase 3: Optimization
1. Performance improvements
2. Advanced security
3. Analytics integration
4. Mobile optimization

This contracts document serves as the complete specification for transforming the current mock-based frontend into a fully functional backend-integrated application with Privy authentication, crypto wallets, and affiliate system.