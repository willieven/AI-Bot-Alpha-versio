from .auth import authenticate_user, get_user_directory
from .file_operations import *

def handle_command(command, session):
    cmd = command.split(' ')[0].upper()
    arg = ' '.join(command.split(' ')[1:])

    if cmd == 'USER':
        return handle_user(session, arg)
    elif cmd == 'PASS':
        return handle_pass(session, arg)
    elif cmd == 'SYST':
        return '215 UNIX Type: L8'
    elif cmd == 'FEAT':
        return handle_feat()
    elif cmd == 'PWD':
        return handle_pwd(session)
    elif cmd == 'CWD':
        return handle_cwd(session, arg)
    # ... implement other command handlers

def handle_user(session, username):
    session.username = username
    return '331 User name okay, need password'

def handle_pass(session, password):
    user_id, user_data = authenticate_user(session.username, password)
    if user_id:
        session.authenticated = True
        session.user_id = user_id
        session.user_data = user_data
        session.base_directory = get_user_directory(user_id)
        return '230 User logged in, proceed'
    else:
        return '530 Login incorrect'

def handle_feat():
    features = [
        '211-Features:',
        ' PASV',
        ' UTF8',
        ' MLSD',
        ' SIZE',
        ' REST STREAM',
        ' MDTM',
        ' MFMT',
        ' TVFS',
        ' AVBL',
        ' EPRT',
        ' EPSV',
        ' ESTP',
        ' ALLO',
        '211 End'
    ]
    return '\r\n'.join(features)

# Implement other command handlers...