from telethon import TelegramClient
import asyncio

# 👇 ВСТАВЬТЕ СВОИ ДАННЫЕ
API_ID = 32023447
API_HASH = 'Oae2e5b97916e78fcbfdce9a76b66979'

async def main():
    client = TelegramClient('session_name', API_ID, API_HASH)
    
    print("📱 Введите номер телефона в формате +7XXXXXXXXXX")
    await client.start()
    
    session_string = client.session.save()
    print("\n" + "=" * 60)
    print("✅ ВАШ SESSION_STRING:")
    print("=" * 60)
    print(session_string)
    print("=" * 60)
    
    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
