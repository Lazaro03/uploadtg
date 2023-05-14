


import asyncio

async def download_media(api_id,api_hash,bot_token,chat_id, message_id):
    try:
        client:TelegramClient = TelegramClient('media_down', api_id=api_id, api_hash=api_hash).start(bot_token=bot_token)

        messages = await client.get_messages()

        await client.disconnect()
    except Exception as ex:
        print('Invalid media ID given!')
