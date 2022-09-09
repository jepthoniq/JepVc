import asyncio
import logging

from jepthon import Config, jepiq
from jepthon.core.managers import edit_delete, edit_or_reply
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import User

from .helper.stream_helper import Stream
from .helper.tg_downloader import tg_dl
from .helper.vcp_helper import jepthonvc 

logging.getLogger("pytgcalls").setLevel(logging.ERROR)

OWNER_ID = jepiq.uid

vc_session = Config.VC_SESSION

if vc_session:
    vc_client = TelegramClient(
        StringSession(vc_session), Config.APP_ID, Config.API_HASH
    )
else:
    vc_client = jepiq

vc_client.__class__.__module__ = "telethon.client.telegramclient"
vc_player = jepthonvc(vc_client)

asyncio.create_task(vc_player.start())


@vc_player.app.on_stream_end()
async def handler(_, update):
    await vc_player.handle_next(update)


ALLOWED_USERS = set()


@jepthon.ar_cmd(pattern="انضم ?(\S+)? ?(?:-as)? ?(\S+)?")
async def joinVoicechat(event):
    chat = event.pattern_match.group(1)
    joinas = event.pattern_match.group(2)

    await edit_or_reply(event, "**- جار الانضمام الى المكالمة الصوتية**")

    if chat and chat != "-ك":
        if chat.strip("-").isnumeric():
            chat = int(chat)
    else:
        chat = event.chat_id

    if vc_player.app.active_calls:
        return await edit_delete(
            event, f"**- انت موجود بالاصل في {vc_player.CHAT_NAME}**"
        )

    try:
        vc_chat = await jepiq.get_entity(chat)
    except Exception as e:
        return await edit_delete(event, f'خطا : \n{e or "دردشة غير معروفة"}')

    if isinstance(vc_chat, User):
        return await edit_delete(
            event, "المكالمات الصوتية غير مفعلة في المجموعات الخاصة"
        )

    if joinas and not vc_chat.username:
        await edit_or_reply(
            event, "**- لم ستم الانضمام بشكل مخفي تم الانضمام بشكل حسابك الاساسي**"
        )
        joinas = False

    out = await vc_player.join_vc(vc_chat, joinas)
    await edit_delete(event, out)


@jepthon.ar_cmd(pattern="غادر")
async def leaveVoicechat(event):
    if vc_player.CHAT_ID:
        await edit_or_reply(event, "جار المغادرة انتظر قليلا ......")
        chat_name = vc_player.CHAT_NAME
        await vc_player.leave_vc()
        await edit_delete(event, f"**- تم بنجاح مغادرة المكالمة من {chat_name}*")
    else:
        await edit_delete(event, "**- انت لم تنضم لأي اتصال اولا**")


@jepiq.ar_cmd(pattern="قائمة_التشغيل")
async def get_playlist(event):
    await edit_or_reply(event, "**- جار التعرف على البيانات انتظر قليلا**")
    playl = vc_player.PLAYLIST
    if not playl:
        await edit_delete(event, "قائمة التشغيل فارغة", time=10)
    else:
        jep = ""
        for num, item in enumerate(playl, 1):
            if item["stream"] == Stream.audio:
                jep += f"{num}. 🔉  `{item['title']}`\n"
            else:
                jep += f"{num}. 📺  `{item['title']}`\n"
        await edit_delete(event, f"**قائمة التشغيل:**\n\n{jep}\n@jepthon")


@jepiq.ar_cmd(pattern="تشغيل_صوتي ?(-ج)? ?([\S ]*)?")
async def play_audio(event):
    flag = event.pattern_match.group(1)
    input_str = event.pattern_match.group(2)
    if input_str == "" and event.reply_to_msg_id:
        input_str = await tg_dl(event)
    if not input_str:
        return await edit_delete(
            event,
            "**- يجب عليك الرد على المقطع الصوتي او كتابة الرابط مع الامر**",
            time=20,
        )
    if not vc_player.CHAT_ID:
        return await edit_or_reply(
            event, "**- يجب عليك الانضمام للمكالمة اولا استخدام الامر**"
        )
    if not input_str:
        return await edit_or_reply(
            event, "**- يجب عليك وضع رابط او الرد على الميديا المراد تشغيلها**"
        )
    await edit_or_reply(event, "**- جار التشغيل في المكالمة انتظر قليلا**")
    if flag:
        resp = await vc_player.play_song(input_str, Stream.audio, force=True)
    else:
        resp = await vc_player.play_song(input_str, Stream.audio, force=False)
    if resp:
        await edit_delete(event, resp, time=30)


@jepiq.ar_cmd(pattern="ايقاف_مؤقت")
async def pause_stream(event):
    await edit_or_reply(event, "**- تم ايقاف التشغيل مؤقتا**")
    res = await vc_player.pause()
    await edit_delete(event, res, time=30)


@jepiq.ar_cmd(pattern="استئناف")
async def resume_stream(event):
    await edit_or_reply(event, "- تم بنجاح استئناف التشغيل")
    res = await vc_player.resume()
    await edit_delete(event, res, time=30)


@jepiq.ar_cmd(pattern="تخطي")
async def skip_stream(event):
    await edit_or_reply(event, "- تم بنجاح تخطي التشغيل الحالي")
    res = await vc_player.skip()
    await edit_delete(event, res, time=30)
