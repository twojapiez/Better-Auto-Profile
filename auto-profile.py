#!/usr/bin/env python3
# Make sure you install dependencies first:
# pip3 install -U steam[client]
# If it doesnt work try running on windows and dont bother with installing dependencies on linux

import json
import time
import random
import steam.client
import string

f = open('accounts.txt', 'r')
data = f.read()
f.close()

data = data.replace('\r\n', '\n')
accounts = data.split('\n')
accounts = [account for account in accounts if account.strip()] 

profile = open('image.jpg', 'rb')
nickname = 'Your nick.'

enable_debugging = False
enable_extra_info = False
enable_avatarchange = False
enable_namechange = True
enable_nameclear = False
enable_set_up = False
enable_gatherid32 = True
dump_response = False
make_commands = True
force_sleep = False
Randomname = True  # Toggle this to generate random account names
InsertRandomChars = True  # Toggle this to insert random characters into the nickname
random_name_length = 10  # Length of the random account name
random_chars = [ '็', '่', '๊', '๋', '์', 'ู']  # Modify this list as you wish currently holds random semi-invis symbols for tf2

def debug(message):
    if enable_debugging:
        print(message)

def extra(message):
    if enable_extra_info:
        print(message)

def insert_random_chars(name, chars, num_insertions):
    name_list = list(name)
    for _ in range(num_insertions):
        pos = random.randint(0, len(name_list))
        char = random.choice(chars)
        name_list.insert(pos, char)
    return ''.join(name_list)

def generate_random_string(length):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

if enable_gatherid32:
    open('steamid32.txt', 'w').close()
    id_file = open('steamid32.txt', 'a')  

for index, account in enumerate(accounts):
    username, password = account.split(':')
    print(f'Logging in as user #{index + 1}/{len(accounts)} ({username})...')

    client = steam.client.SteamClient()
    eresult = client.login(username, password=password)
    status = 'OK' if eresult == 1 else 'FAIL'
    print(f'Login status: {status} ({eresult})')
    if status == 'FAIL':
        raise RuntimeError(
            'Login failed; bailing out. See https://steam.readthedocs.io/en/stable/api/steam.enums.html#steam.enums'
            '.common.EResult for the relevant error code.')

    print(f'Logged in as: {client.user.name}')
    print(f'Community profile: {client.steam_id.community_url}')
    extra(f'Last logon (UTC): {client.user.last_logon}')
    extra(f'Last logoff (UTC): {client.user.last_logoff}')

    if enable_gatherid32:
        id32 = str(client.steam_id.as_32)
        if make_commands:
            id_file.write(f'cat_pl_add_id {id32} CAT\n')
            print('Saved the SteamID32 as a Cathook change playerstate command.')
        else:
            id_file.write(f'{id32}\n')
            print('Saved the SteamID32 as raw.')

    if enable_namechange:
        if Randomname:
            nickname = generate_random_string(random_name_length)
        if InsertRandomChars:
            nickname = insert_random_chars(nickname, random_chars, 3)  
        time.sleep(5) 
        client.change_status(persona_state=1, player_name=nickname)
        print(f'Changed Steam nickname to "{nickname}"')

    if enable_avatarchange or enable_nameclear or enable_set_up:
        print('Getting web_session...')
        session = client.get_web_session()
        if session is not None:
            debug(f'session.cookies: {session.cookies}')

            if enable_avatarchange:
                url = 'https://steamcommunity.com/actions/FileUploader'
                id64 = client.steam_id.as_64  # type int
                data = {
                    'MAX_FILE_SIZE': '1048576',
                    'type': 'player_avatar_image',
                    'sId': str(id64),
                    'sessionid': session.cookies.get('sessionid', domain='steamcommunity.com'),
                    'doSub': '1',
                }
                post_cookies = {
                    'sessionid': session.cookies.get('sessionid', domain='steamcommunity.com'),
                    'steamLoginSecure': session.cookies.get('steamLoginSecure', domain='steamcommunity.com')
                }

                print('Setting profile picture...')

                r = session.post(url=url, params={'type': 'player_avatar_image', 'sId': str(id64)},
                                files={'avatar': profile},
                                data=data, cookies=post_cookies)
                content = r.content.decode('ascii')
                if dump_response:
                    print(f'response: {content}')
                if not content.startswith('<!DOCTYPE html'):
                    response = json.loads(content)
                    if 'message' in response:
                        raise RuntimeError(f'Error setting profile: {response["message"]}')

            if enable_nameclear:
                print('Clearing nickname history...')
                id64 = client.steam_id.as_64
                r = session.post(f'https://steamcommunity.com/my/ajaxclearaliashistory/',
                                 data={'sessionid': session.cookies.get('sessionid', domain='steamcommunity.com')},
                                 cookies={'sessionid': session.cookies.get('sessionid', domain='steamcommunity.com'),
                                          'steamLoginSecure': session.cookies.get('steamLoginSecure',
                                                                                  domain='steamcommunity.com')})

            if enable_set_up:
                print('Setting up community profile...')
                r = session.post(f'https://steamcommunity.com/my/edit?welcomed=1',
                                 data={'sessionid': session.cookies.get('sessionid', domain='steamcommunity.com')},
                                 cookies={'sessionid': session.cookies.get('sessionid', domain='steamcommunity.com'),
                                          'steamLoginSecure': session.cookies.get('steamLoginSecure',
                                                                                  domain='steamcommunity.com')})

        else:
            print("Failed to create a session. Check your authentication or network.")

    print('Done; logging out.')
    client.logout()
    profile.seek(0)
    print()
    if ((enable_avatarchange or enable_set_up) and (index + 1 != len(accounts) or len(accounts) <= 10)) or force_sleep:
        time.sleep(31)
if enable_gatherid32:
    id_file.close()
profile.close()
print('Done.')
