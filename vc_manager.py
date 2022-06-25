from userbot import catub
from userbot.core.managers import edit_delete, edit_or_reply
from userbot.helpers.utils import mentionuser
from telethon.tl.types import User, Channel, Chat
from telethon import functions
from telethon.errors import ChatAdminRequiredError, UserAlreadyInvitedError

plugin_category = "extra"


async def get_group_call(chat):
    if isinstance(chat, Channel):
        result = await catub(functions.channels.GetFullChannelRequest(
            channel=chat
        ))
    elif isinstance(chat, Chat):
        result = await catub(functions.messages.GetFullChatRequest(
            chat_id=chat.id
        ))
    return result.full_chat.call


async def parse_entity(entity):
    if entity.isnumeric():
        entity = int(entity)
    return await catub.get_entity(entity)


@catub.cat_cmd(
    pattern="gcstart",
    command=("gcstart", plugin_category),
)
async def start_vc(event):
    "To start a Voice Chat."
    chat = event.chat_id
    await edit_or_reply(event, 'Starting Group Call')
    vc_chat = await catub.get_entity(chat)
    if isinstance(chat, User):
        return await edit_delete(event, "Voice Chats are not available in Private Chats")

    gc_call = await get_group_call(vc_chat)

    if gc_call:
        return await edit_delete(event, 'Group Call is already available in this chat')

    try:
        await catub(functions.phone.CreateGroupCallRequest(
            peer=vc_chat,
            title='Cat VC',
        ))
        await edit_delete(event, f'Started Group Call')
    except ChatAdminRequiredError:
        await edit_delete(event, "You should be chat admin to start vc", time=20)


@catub.cat_cmd(
    pattern="gcend",
    command=("gcend", plugin_category),
)
async def end_vc(event):
    "To end a Voice Chat."
    chat = event.chat_id
    await edit_or_reply(event, 'Ending Group Call')

    vc_chat = await catub.get_entity(chat)
    if isinstance(chat, User):
        return await edit_delete(event, "Voice Chats are not available in Private Chats")

    gc_call = await get_group_call(vc_chat)

    if not gc_call:
        return await edit_delete(event, 'No Group Call in this chat')

    try:
        await catub(functions.phone.DiscardGroupCallRequest(
            call=gc_call
        ))
        await edit_delete(event, f'Group Call Ended')
    except ChatAdminRequiredError:
        await edit_delete(event, "You should be chat admin to start vc", time=20)


@catub.cat_cmd(
    pattern="gcinv ?(.*)?",
    command=("gcinv", plugin_category),
)
async def inv_vc(event):
    "To invite users to vc."
    chat = event.chat_id
    users = event.pattern_match.group(1)
    await edit_or_reply(event, 'Inviting User to Group Call')
    if users:
        entities = users.split(' ')
        users = []
        for entity in entities:
            cc = await parse_entity(entity)
            if isinstance(cc, User):
                users.append(cc)
    elif event.reply_to_msg_id:
        reply = await event.get_reply_message()
        users = [reply.from_id]

    if not users:
        return await edit_delete('Whom Should i invite')

    try:
        vc_chat = await catub.get_entity(chat)
    except Exception as e:
        return await edit_delete(event, f'ERROR : \n{e or "UNKNOWN CHAT"}')

    gc_call = await get_group_call(vc_chat)

    if not gc_call:
        return await edit_delete(event, 'No Group Call in this chat')

    try:
        await catub(functions.phone.InviteToGroupCallRequest(
            call=gc_call,
            users=users
        ))
        await edit_delete(event, f'Invited users to Group Call')
    except UserAlreadyInvitedError:
        return await edit_delete(event, "User is Already Invited", time=20)


@catub.cat_cmd(
    pattern="gcinfo",
    command=("gcinfo", plugin_category),
)
async def inv_vc(event):
    "Get info of VC."
    chat = event.chat_id
    await edit_or_reply(event, 'Getting Group Call Info')
    try:
        vc_chat = await catub.get_entity(chat)
    except Exception as e:
        return await edit_delete(event, f'ERROR : \n{e or "UNKNOWN CHAT"}')

    gc_call = await get_group_call(vc_chat)

    if not gc_call:
        return await edit_delete(event, 'No Group Call in this chat')

    call_details = await catub(functions.phone.GetGroupCallRequest(
        call=gc_call,
        limit=1
    ))

    grp_call = "**Group Call Info**\n\n"
    grp_call += f"**Title :** {call_details.call.title}\n"
    grp_call += f"**Participants Count :** {call_details.call.participants_count}\n\n"

    if call_details.call.participants_count > 0:
        grp_call += "**Participants**\n"
        for user in call_details.users:
            nam = f"{user.first_name or ''} {user.last_name or ''}"
            grp_call += f"  ● {mentionuser(nam,user.id)} - `{user.id}`\n"
    await edit_or_reply(event, grp_call)


@catub.cat_cmd(
    pattern="gctitle?(.*)?",
    command=("gctitle", plugin_category),
)
async def inv_vc(event):
    "To change vc title."
    chat = event.chat_id
    title = event.pattern_match.group(1)
    await edit_or_reply(event, 'Changing Group Call Title')
    if not title:
        return await edit_delete("What should i keep as title")

    vc_chat = await catub.get_entity(chat)
    if isinstance(chat, User):
        return await edit_delete(event, "Voice Chats are not available in Private Chats")

    gc_call = await get_group_call(vc_chat)

    if not gc_call:
        return await edit_delete(event, 'No Group Call in this chat')

    await catub(functions.phone.EditGroupCallTitleRequest(
        call=gc_call,
        title=title
    ))
    await edit_delete(event, f"VC title was changed to **{title}**")


@catub.cat_cmd(
    pattern="gcmute ?(.*)?",
    command=("gcmute", plugin_category),
)
async def mute_vc(event):
    "To mute users in vc."
    chat = event.chat_id
    users = event.pattern_match.group(1)
    await edit_or_reply(event, 'Muting User in Group Call')
    if users:
        entities = users.split(' ')
        users = []
        for entity in entities:
            cc = await parse_entity(entity)
            if isinstance(cc, User):
                users.append(cc)
    elif event.reply_to_msg_id:
        reply = await event.get_reply_message()
        users = [reply.from_id]

    if not users:
        return await edit_delete('Whom Should i mute')

    vc_chat = await catub.get_entity(chat)
    if isinstance(chat, User):
        return await edit_delete(event, "Voice Chats are not available in Private Chats")

    gc_call = await get_group_call(vc_chat)

    if not gc_call:
        return await edit_delete(event, 'No Group Call in this chat')

    for user in users:
        await catub(functions.phone.EditGroupCallParticipantRequest(
            call=gc_call,
            participant=user,
            muted=True,
        ))
    await edit_delete(event, f'Muted users in Group Call')


@catub.cat_cmd(
    pattern="gcunmute ?(.*)?",
    command=("gcunmute", plugin_category),
)
async def unmute_vc(event):
    "To unmute users in vc."
    chat = event.chat_id
    users = event.pattern_match.group(1)
    await edit_or_reply(event, 'Unmuting User in Group Call')
    if users:
        entities = users.split(' ')
        users = []
        for entity in entities:
            cc = await parse_entity(entity)
            if isinstance(cc, User):
                users.append(cc)
    elif event.reply_to_msg_id:
        reply = await event.get_reply_message()
        users = [reply.from_id]

    if not users:
        return await edit_delete('Whom Should i unmute')

    vc_chat = await catub.get_entity(chat)
    if isinstance(chat, User):
        return await edit_delete(event, "Voice Chats are not available in Private Chats")

    gc_call = await get_group_call(vc_chat)

    if not gc_call:
        return await edit_delete(event, 'No Group Call in this chat')

    for user in users:
        await catub(functions.phone.EditGroupCallParticipantRequest(
            call=gc_call,
            participant=user,
            muted=False,
        ))
    await edit_delete(event, f'Unmuted users in Group Call')
