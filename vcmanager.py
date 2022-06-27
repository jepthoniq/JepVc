from telethon import functions
from telethon.errors import ChatAdminRequiredError, UserAlreadyInvitedError
from telethon.tl.types import Channel, Chat, User
from userbot import catub
from userbot.core.managers import edit_delete, edit_or_reply
from userbot.helpers.utils import mentionuser

plugin_category = "extra"


async def chat_vc_checker(event, chat, edits=True):
    if isinstance(chat, User):
        await edit_delete(event, "Voice Chats are not available in Private Chats")
        return None
    elif isinstance(chat, Channel):
        result = (
            await catub(functions.channels.GetFullChannelRequest(channel=chat))
        ).full_chat.call
    elif isinstance(chat, Chat):
        result = (
            await catub(functions.messages.GetFullChatRequest(chat_id=chat.id))
        ).full_chat.call
    if not result:
        if edits:
            await edit_delete(event, "No Group Call in this chat")
        return None
    return result


async def parse_entity(entity):
    if entity.isnumeric():
        entity = int(entity)
    return await catub.get_entity(entity)


@catub.cat_cmd(
    pattern="vcstart",
    command=("vcstart", plugin_category),
)
async def start_vc(event):
    "To start a Voice Chat."
    vc_chat = await catub.get_entity(event.chat_id)
    gc_call = await chat_vc_checker(event, vc_chat, False)
    if gc_call:
        return await edit_delete(event, "Group Call is already available in this chat")
    try:
        await catub(
            functions.phone.CreateGroupCallRequest(
                peer=vc_chat,
                title="Cat VC",
            )
        )
        await edit_delete(event, "Started Group Call")
    except ChatAdminRequiredError:
        await edit_delete(event, "You should be chat admin to start vc", time=20)


@catub.cat_cmd(
    pattern="vcend",
    command=("vcend", plugin_category),
)
async def end_vc(event):
    "To end a Voice Chat."
    vc_chat = await catub.get_entity(event.chat_id)
    gc_call = await chat_vc_checker(event, vc_chat)
    if not gc_call:
        return
    try:
        await catub(functions.phone.DiscardGroupCallRequest(call=gc_call))
        await edit_delete(event, "Group Call Ended")
    except ChatAdminRequiredError:
        await edit_delete(event, "You should be chat admin to kill vc", time=20)


@catub.cat_cmd(
    pattern="vcinv ?(.*)?",
    command=("vcinv", plugin_category),
)
async def inv_vc(event):
    "To invite users to vc."
    users = event.pattern_match.group(1)
    if not users:
        return await edit_delete("Whom Should i invite")
    vc_chat = await catub.get_entity(event.chat_id)
    gc_call = await chat_vc_checker(event, vc_chat)
    if not gc_call:
        return
    await edit_or_reply(event, "Inviting User to Group Call")
    if users:
        entities = users.split(" ")
        users = []
        for entity in entities:
            cc = await parse_entity(entity)
            if isinstance(cc, User):
                users.append(cc)
    elif event.reply_to_msg_id:
        reply = await event.get_reply_message()
        users = [reply.from_id]
    try:
        await catub(functions.phone.InviteToGroupCallRequest(call=gc_call, users=users))
        await edit_delete(event, "Invited users to Group Call")
    except UserAlreadyInvitedError:
        return await edit_delete(event, "User is Already Invited", time=20)


@catub.cat_cmd(
    pattern="vcinfo",
    command=("vcinfo", plugin_category),
)
async def info_vc(event):
    "Get info of VC."
    await edit_or_reply(event, "Getting Group Call Info")
    vc_chat = await catub.get_entity(event.chat_id)
    gc_call = await chat_vc_checker(event, vc_chat)
    if not gc_call:
        return
    call_details = await catub(
        functions.phone.GetGroupCallRequest(call=gc_call, limit=1)
    )
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
    pattern="vctitle?(.*)?",
    command=("vctitle", plugin_category),
)
async def title_vc(event):
    "To change vc title."
    title = event.pattern_match.group(1)
    await edit_or_reply(event, "Changing Group Call Title")
    if not title:
        return await edit_delete("What should i keep as title")
    vc_chat = await catub.get_entity(event.chat_id)
    gc_call = await chat_vc_checker(event, vc_chat)
    if not gc_call:
        return
    await catub(functions.phone.EditGroupCallTitleRequest(call=gc_call, title=title))
    await edit_delete(event, f"VC title was changed to **{title}**")


@catub.cat_cmd(
    pattern="vc(|un)mute ([\s\S]*)",
    command=("vcmute", plugin_category),
)
async def mute_vc(event):
    "To mute users in vc."
    cmd = event.pattern_match.group(1)
    users = event.pattern_match.group(2)
    check = "Unmute" if cmd else "Mute"
    if not users:
        return await edit_delete(f"Whom Should i {check}")
    vc_chat = await catub.get_entity(event.chat_id)
    gc_call = await chat_vc_checker(event, vc_chat)
    if not gc_call:
        return

    await edit_or_reply(event, f"{check[:-1]}ing User in Group Call")
    if users:
        entities = users.split(" ")
        users = []
        for entity in entities:
            cc = await parse_entity(entity)
            if isinstance(cc, User):
                users.append(cc)
    elif event.reply_to_msg_id:
        reply = await event.get_reply_message()
        users = [reply.from_id]

    for user in users:
        await catub(
            functions.phone.EditGroupCallParticipantRequest(
                call=gc_call,
                participant=user,
                muted=bool(not cmd),
            )
        )
    await edit_delete(event, f"{check}d users in Group Call")


@catub.cat_cmd(
    command=("vcunmute", plugin_category),
)
async def unmute_vc(event):
    "To unmute users in vc."
