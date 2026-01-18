from app.utils.jwt import create_access_token
from app.models import User, OAuthProvider
from app.database import get_db
import asyncio
import uuid

async def create_test_user():
    async for db in get_db():
        # Create a real test user in the database
        user = User(
            email="test@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="test_oauth_123"
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        # Generate token for this user
        token = create_access_token(user.id, user.email)
        print(f"{token}")
        print(f"# USER_ID={user.id}")
        return user.id, token

asyncio.run(create_test_user())
