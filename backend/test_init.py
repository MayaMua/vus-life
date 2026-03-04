import asyncio
import httpx
from app.api.main import app

async def test():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        print("Testing /health...")
        response = await client.get("/health")
        print("Health status:", response.status_code)
        
        print("Testing /api/settings/...")
        response = await client.get("/api/settings/")
        print("Settings status:", response.status_code)
        print("Settings body:", response.json())

if __name__ == "__main__":
    asyncio.run(test())
