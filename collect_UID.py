from pyrogram import Client, raw, errors

from pyrogram.scaffold import Scaffold

import asyncio

import redis


query = redis.StrictRedis(
    host='localhost',
    port=6379,
    db=1,
    decode_responses=True
)  



async def validate_link(app, group):
    if "joinchat" in group:
        try:
            match = Scaffold.INVITE_LINK_RE.match(group)

            chat = await app.send(
                raw.functions.messages.ImportChatInvite(
                    hash=match.group(1)
                )
            )
            chat_id = chat["chats"][0]["id"]
            resp = str(chat_id)

        except errors.UserAlreadyParticipant:
            chat = await app.get_chat(group)
            resp = str(chat.id)

        except errors.UsernameInvalid:
            resp = "Error: User name Invalid."
    
        except errors.InviteHashExpired:
            resp = "Error: INVITE HASH EXPIRED."

        except errors.UsernameNotOccupied:
            resp = "Error: Username Not Occupied."

        except errors.FloodWait as wait:
            resp = f"Error: Flood Wait : {wait.x} Second."
    
        except Exception as err:
            resp = f"Error: Undefined error!!, {err}."

    else:
        resp = group
	
    return resp



async def collect_members(
        app,
        session_name:str,
        group:str,
        querys:list,
        start_range:int,
        end_range:int):

    try:
        empty = 0
        if await app.connect() == True:
            chat = await asyncio.create_task(validate_link(app, group))
            
            if chat.startswith("Error:"):
                return chat

            peer = await app.resolve_peer(chat)
            
            if isinstance(peer, raw.types.InputPeerChannel):
                for q in querys:
                    offset=0 
                    filter_ = raw.types.ChannelParticipantsSearch(q=q)

                    if filter_.q == " ":
                        if empty == 1:
                            continue
                        else:
                            empty = 1

                    for i in range(start_range, end_range, 200):
                        r = await app.send(raw.functions.channels.GetParticipants(
                                channel=peer,
                                filter=filter_,
                                offset=offset,
                                limit=202,
                                hash=0 
                            ),
                        sleep_threshold=20
                        )

                        for member in r.users: 
                            query.sadd("Available:Users-InputPeer", f"{member.id}:{member.access_hash}")

                        offset += len(r.users)

                        print(f"Successfully scrap {len(r.users)} user, start range {start_range}, end range {end_range}, query: {q}")

                        if len(r.users) == 0:
                            break
					
                    start_range += 10000
                    end_range   += 10000
    
                return f"Successfully collect {query.scard('Available:Users-InputPeer')} user from {group}"
        else:
            return "Session is deactivated"

    except errors.UserDeactivatedBan as err:
        return f"Error: Session: {session_name} Deactivated Ban"

    except errors.UserDeactivated as err:
        return f"Error: Session: {session_name} Deactivated"

    except errors.Unauthorized as err:
        return f"Error: Session: {session_name} Unauthorized"
        
    except errors.AuthKeyUnregistered as err:
        return f"Session: {session_name} Auth Key Unregistered"



async def main():
    en_char  = 'a b c d e f g h i j k l m n o p q r s t u v w x y z'
    per_char = 'چ ج ح خ ه ع غ ف ق ث ص ض ش س ی ب ل ا ت ن م ک گ و پ د ذ ر ز ط ظ'
    int_char = '0 1 2 3 4 5 6 7 8 9'	
	
    query_ =  en_char + int_char + per_char

    session_name = "collect_members"

    group = input("Please Enter The link: ")

    start_range = 0

    end_range = 10000

	
    app = Client(
        session_name = session_name,
        config_file = "config.ini",
        no_updates = True
	)	
	
    resp = await asyncio.create_task(
        collect_members(
            app=app,
            session_name=session_name, 
            group=group,
            querys=query_,
            start_range=start_range,
            end_range=end_range
        )
	)

    print(resp)

asyncio.run(main())


