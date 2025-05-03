from telethon import TelegramClient, events, Button
from telethon.tl.functions.account import ReportPeerRequest
from telethon.tl.types import (
    InputReportReasonSpam,
    InputReportReasonFake,
    InputReportReasonViolence,
    InputReportReasonPornography,
    InputReportReasonChildAbuse,
    InputReportReasonCopyright,
    InputReportReasonIllegalDrugs,
    InputReportReasonPersonalDetails,
    InputReportReasonOther
)
from telethon.errors import SessionPasswordNeededError
import asyncio
import json
import os

# Configuration
BOT_TOKEN = '7570504943:AAHK0Nfs3fYfPsxvumovcIn29ML78EZB6LA'

# List of admin IDs
ADMIN_IDS = [6985505204, 6935400972 ,6715519631] # Add more admin IDs here

# Initialize bot
API_ID = '22209926'
API_HASH = '04ee2355de0883331fa6168dfb6e9b24'
bot = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Store sessions and configuration
clients = {}

@bot.on(events.NewMessage(pattern='/add_admin'))
async def add_admin_handler(event):
    if event.sender_id not in ADMIN_IDS:
        await event.respond("You are not authorized to use this command.")
        return
    
    try:
        new_admin_id = int(event.text.split()[1])
        if new_admin_id in ADMIN_IDS:
            await event.respond("This user is already an admin.")
            return
        
        ADMIN_IDS.append(new_admin_id)
        await event.respond(f"Added {new_admin_id} as admin successfully!")
    except (IndexError, ValueError):
        await event.respond("Please use the format: /add_admin USER_ID")

@bot.on(events.NewMessage(pattern='/remove_admin'))
async def remove_admin_handler(event):
    if event.sender_id not in ADMIN_IDS:
        await event.respond("You are not authorized to use this command.")
        return
    
    try:
        admin_id = int(event.text.split()[1])
        if admin_id not in ADMIN_IDS:
            await event.respond("This user is not an admin.")
            return
        
        ADMIN_IDS.remove(admin_id)
        await event.respond(f"Removed {admin_id} from admins successfully!")
    except (IndexError, ValueError):
        await event.respond("Please use the format: /remove_admin USER_ID")

@bot.on(events.NewMessage(pattern='/list_admins'))
async def list_admins_handler(event):
    if event.sender_id not in ADMIN_IDS:
        await event.respond("You are not authorized to use this command.")
        return
        
    admin_list = "\n".join([f"• {admin_id}" for admin_id in ADMIN_IDS])
    await event.respond(f"Current admin IDs:\n{admin_list}")

user_states = {}

# Report reasons mapping
REPORT_REASONS = {
    "SPAM": (InputReportReasonSpam, "Spam"),
    "FAKE": (InputReportReasonFake, "Fake Account"),
    "VIOLENCE": (InputReportReasonViolence, "Violence"),
    "PORN": (InputReportReasonPornography, "Adult Content"),
    "CHILD_ABUSE": (InputReportReasonChildAbuse, "Child Abuse"),
    "COPYRIGHT": (InputReportReasonCopyright, "Copyright"),
    "DRUGS": (InputReportReasonIllegalDrugs, "Illegal Drugs"),
    "PERSONAL": (InputReportReasonPersonalDetails, "Personal Details"),
    "OTHER": (InputReportReasonOther, "Other")
}

@bot.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    if event.sender_id not in ADMIN_IDS:
        await event.respond("You are not authorized to use this bot.")
        return

    await event.respond(
        "Welcome to Multi-Account Mass Report Bot!\n\nChoose an option:",
        buttons=[
            [Button.text("➕ Add Account"), Button.text("📊 Accounts Status")],
            [Button.text("🎯 Start Mass Report"), Button.text("❌ Remove Account")]
        ]
    )

@bot.on(events.NewMessage(pattern='^➕ Add Account$'))
async def add_account_handler(event):
    if event.sender_id not in ADMIN_IDS:
        return
    user_states[event.sender_id] = {'state': 'waiting_phone'}
    await event.respond("Please send the phone number (format: +1234567890)")

@bot.on(events.NewMessage(pattern='^📊 Accounts Status$'))
async def accounts_status_handler(event):
    if event.sender_id not in ADMIN_IDS:
        return

    if not clients:
        await event.respond("No accounts added yet.")
        return

    status = "Connected Accounts:\n\n"
    for phone in clients.keys():
        status += f"📱 {phone}: Connected\n"

    await event.respond(status)

@bot.on(events.NewMessage(pattern='^❌ Remove Account$'))
async def remove_account_handler(event):
    if event.sender_id not in ADMIN_IDS:
        return

    if not clients:
        await event.respond("No accounts to remove.")
        return

    buttons = [[Button.text(f"❌ {phone}")] for phone in clients.keys()]
    await event.respond("Select account to remove:", buttons=buttons)

@bot.on(events.NewMessage(pattern='^❌ \+\d+$'))
async def handle_remove_selection(event):
    if event.sender_id not in ADMIN_IDS:
        return
    phone = event.text[2:]
    if phone in clients:
        await clients[phone].disconnect()
        del clients[phone]
        await event.respond(f"✅ Account {phone} removed!")
    await start_handler(event)

@bot.on(events.NewMessage(pattern='^🎯 Start Mass Report$'))
async def start_report_handler(event):
    if event.sender_id not in ADMIN_IDS:
        return

    if not clients:
        await event.respond("No accounts added. Please add accounts first.")
        return

    keyboard = [
        [Button.text("👤 User"), Button.text("📢 Channel")],
        [Button.text("👥 Group"), Button.text("🤖 Bot")],
        [Button.text("📌 Message")]
    ]

    user_states[event.sender_id] = {'state': 'choosing_target_type'}
    await event.respond("Choose what to report:", buttons=keyboard)

@bot.on(events.NewMessage(pattern='^(👤 User|📢 Channel|👥 Group|🤖 Bot|📌 Message)$'))
async def handle_report_type(event):
    if event.sender_id not in ADMIN_IDS:
        return

    report_type = event.text
    user_states[event.sender_id] = {
        'state': 'waiting_target',
        'report_type': report_type
    }

    if report_type == "📌 Message":
        await event.respond("Please send the message link (e.g., https://t.me/channel/123)")
    else:
        await event.respond("Please send the username or ID (e.g., @username)")

@bot.on(events.NewMessage)
async def message_handler(event):
    if event.sender_id not in ADMIN_IDS:
        return

    if event.sender_id in user_states:
        state = user_states[event.sender_id]

        # Handle phone number input
        if state.get('state') == 'waiting_phone':
            await handle_phone_number(event)
            return

        # Handle verification code input
        if state.get('state') == 'waiting_code':
            await handle_verification_code(event)
            return

        # Handle 2FA password input
        if state.get('state') == 'waiting_password':
            await handle_2fa_password(event)
            return

        # Handle username/ID input
        if state.get('state') == 'waiting_target':
            target = event.text.strip()
            if not target.startswith('@') and not target.isdigit():
                await event.respond("Please send a valid username (starting with @) or numeric ID.")
                return
            state['target'] = target
            # Ask for report reason
            reason_buttons = [
                [Button.text(reason[1])] for reason in REPORT_REASONS.values()
            ]
            user_states[event.sender_id]['state'] = 'waiting_reason'
            await event.respond("Select the reason for reporting:", buttons=reason_buttons)
            return

        # Handle report reason selection
        if state.get('state') == 'waiting_reason':
            reason_text = event.text.strip()
            reason_key = None
            for k, v in REPORT_REASONS.items():
                if v[1].lower() == reason_text.lower():
                    reason_key = k
                    break
            if not reason_key:
                await event.respond("Invalid reason. Please select from the buttons.")
                return
            state['reason'] = reason_key
            user_states[event.sender_id]['state'] = 'waiting_report_count'
            await event.respond("How many times do you want to report this target with each account? (Enter a number)")
            return

        # New: Handle number of reports
        if state.get('state') == 'waiting_report_count':
            try:
                count = int(event.text.strip())
                if count < 1 or count > 100:
                    await event.respond("Please enter a number between 1 and 100.")
                    return
                state['report_count'] = count
                user_states[event.sender_id]['state'] = 'waiting_confirm'
                await event.respond(
                    f"Ready to report {state['target']} as {state['report_type']} for {REPORT_REASONS[state['reason']][1]}, {count} times per account. Please confirm to proceed with 'yes'."
                )
            except ValueError:
                await event.respond("Please enter a valid number.")
            return

        # Handle confirmation
        if state.get('state') == 'waiting_confirm':
            if event.text.lower() in ['yes', 'y', 'confirm']:
                await event.respond(f"Reporting {state['target']} as {state['report_type']} for {REPORT_REASONS[state['reason']][1]}...")
                await perform_mass_report(event, state)
                del user_states[event.sender_id]
                await start_handler(event)
            else:
                await event.respond("Report cancelled.")
                del user_states[event.sender_id]
                await start_handler(event)
            return

async def handle_phone_number(event):
    phone = event.text
    if not (phone.startswith("+") and phone[1:].isdigit()):
        await event.respond("Invalid phone number format. Please use: +1234567890")
        return

    try:
        client = TelegramClient(f'session_{phone}', API_ID, API_HASH)
        await client.connect()

        if await client.is_user_authorized():
            clients[phone] = client
            await event.respond("Account already authorized and added successfully!")
        else:
            await client.send_code_request(phone)
            user_states[event.sender_id] = {
                'state': 'waiting_code',
                'phone': phone,
                'client': client
            }
            await event.respond("Please send the verification code you received")

    except Exception as e:
        await event.respond(f"Error: {str(e)}")
        user_states[event.sender_id] = {'state': 'idle'}

async def handle_verification_code(event):
    state = user_states[event.sender_id]
    try:
        await state['client'].sign_in(state['phone'], event.text)
        clients[state['phone']] = state['client']
        await event.respond("Account added successfully!")
        del user_states[event.sender_id]
        await start_handler(event)
    except SessionPasswordNeededError:
        user_states[event.sender_id]['state'] = 'waiting_password'
        await event.respond("This account has 2-step verification enabled. Please send the password.")
    except Exception as e:
        await event.respond(f"Error: {str(e)}")
        del user_states[event.sender_id]
        await start_handler(event)

async def handle_2fa_password(event):
    state = user_states[event.sender_id]
    try:
        if event.text.lower() == "cancel":
            await event.respond("2FA process cancelled.")
            del user_states[event.sender_id]
            await start_handler(event)
            return
        await state['client'].sign_in(password=event.text)
        clients[state['phone']] = state['client']
        await event.respond("Account added successfully (2FA)!")
        del user_states[event.sender_id]
        await start_handler(event)
    except Exception as e:
        await event.respond(f"Error: {str(e)}\nPlease try entering the password again.")

async def perform_mass_report(event, state):
    target = state['target']
    reason_key = state['reason']
    reason_class = REPORT_REASONS[reason_key][0]
    report_count = state.get('report_count', 1)
    success = 0
    failed = 0
    for phone, client in clients.items():
        for _ in range(report_count):
            try:
                entity = await client.get_entity(target)
                await client(ReportPeerRequest(
                    peer=entity,
                    reason=reason_class(),
                    message="Reported via Multi-Account Mass Report Bot"
                ))
                success += 1
            except Exception as e:
                failed += 1
    await event.respond(f"Report finished!\n\n✅ Success: {success}\n❌ Failed: {failed}")

def main():
    print("Bot started...")
    bot.run_until_disconnected()

if __name__ == "__main__":
    main()
