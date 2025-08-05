# users/utils.py

import logging
from django.conf import settings
from students.models import Class, Student
# from twilio.rest import Client # REMOVE OR COMMENT OUT THIS LINE
import africastalking # Keep this import for AfricasTalking

from django.core.mail import EmailMessage # Keep this for email functionality

logger = logging.getLogger(__name__)

def send_sms_notification(recipient_number, message_body):
    """
    Sends an SMS message using AfricasTalking.
    Returns True if successful, False otherwise.
    """
    # Check for AfricasTalking credentials
    if not all([settings.AFRICASTALKING_USERNAME, settings.AFRICASTALKING_API_KEY]):
        logger.error("AfricasTalking credentials (USERNAME or API_KEY) are not set in settings.py. SMS cannot be sent.")
        return False

    try:
        # Initialize AfricasTalking SDK (do this once)
        africastalking.initialize(settings.AFRICASTALKING_USERNAME, settings.AFRICASTALKING_API_KEY)
        sms = africastalking.SMS

        sender_id = getattr(settings, 'AFRICASTALKING_SENDER_ID', settings.AFRICASTALKING_USERNAME)

        # Send the SMS
        response = sms.send(message_body, [recipient_number], sender_id)

        # Log the full response from AfricasTalking for debugging
        print(f"DEBUG: AfricasTalking SMS response for {recipient_number}: {response}")
        # Parse AfricasTalking's response to determine success
        if response and 'SMSMessageData' in response and 'Recipients' in response['SMSMessageData']:
            for recipient_data in response['SMSMessageData']['Recipients']:
                if recipient_data['status'] == 'Success':
                    logger.info(f"SMS successfully queued to {recipient_number} via AfricasTalking. MessageId: {recipient_data['messageId']}")
                    return True
                else:
                    logger.error(
                        f"Failed to send SMS to {recipient_number} via AfricasTalking. "
                        f"Status: {recipient_data['status']}, "
                        f"StatusCode: {recipient_data.get('statusCode', 'N/A')}, "
                        f"MessageId: {recipient_data.get('messageId', 'N/A')}"
                    )
                    return False # Return False if any recipient failed
            # If loop finishes without returning True (e.g., empty recipients list or all non-success)
            logger.error(f"AfricasTalking SMS sending failed, no successful recipients found in response for {recipient_number}.")
            return False
        else:
            logger.error(f"AfricasTalking SMS sending failed, unexpected response structure for {recipient_number}. Full response: {response}")
            return False

    except Exception as e: # This is the change: catching general 'Exception'
        logger.error(f"An error occurred while sending SMS to {recipient_number} via AfricasTalking: {e}")
        return False

# --- Admin Email Notification Function (KEEP AS IS) ---
def send_admin_new_user_notification_email(user):
    """
    Sends an email notification to ADMINS when a new user registers.
    Returns True if successful, False otherwise.
    """
    subject = f"New User Registration: {user.username} - Awaiting Approval"

    # Construct the email body with user details and admin link
    message_body = (
        f"A new user has registered on Sibwesa Primary School and is awaiting approval.\n\n"
        f"User Details:\n"
        f"Username: {user.username}\n"
        f"Email: {user.email}\n"
        f"Phone Number: {user.phone_number if user.phone_number else 'N/A'}\n"
        f"Role: {user.role}\n\n"
        f"Please log in to the admin panel to review and activate their account.\n"
        f"Admin URL: http://127.0.0.1:8000/admin/users/customuser/{user.id}/change/" # Make sure this URL matches your admin path
    )

    # Set the sender email (from settings, or a default fallback)
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'webmaster@localhost')

    # Extract just the email addresses from the ADMINS tuple list
    recipient_list = [admin_tuple[1] for admin_tuple in settings.ADMINS]

    # Check if there are recipients to send to
    if not recipient_list:
        logger.warning("No ADMINS email addresses configured in settings.py. Admin email notification skipped.")
        return False

    try:
        email = EmailMessage(
            subject,
            message_body,
            from_email,
            recipient_list
        )
        email.send(fail_silently=False) # fail_silently=False will raise exceptions on failure
        logger.info(f"Admin notification email sent for new user: {user.username}")
        return True
    except Exception as e:
        logger.error(f"Failed to send admin notification email for new user {user.username}: {e}")
        return False

# --- Admin SMS Notification Function (KEEP AS IS) ---
def send_admin_new_user_notification_sms(user):
    """
    Sends an SMS notification to all ADMIN_PHONE_NUMBERS when a new user registers.
    Returns True if at least one SMS was successfully sent, False otherwise.
    """
    # Check if admin phone numbers are configured
    if not hasattr(settings, 'ADMIN_PHONE_NUMBERS') or not settings.ADMIN_PHONE_NUMBERS:
        logger.warning("ADMIN_PHONE_NUMBERS not configured in settings.py. Admin SMS notification skipped.")
        return False

    # Craft the SMS message (keep it concise for SMS)
    sms_body = f"New user {user.username} ({user.phone_number if user.phone_number else user.email}) registered. Awaiting approval. Check admin panel."

    sent_any_successfully = False
    # Iterate through all configured admin phone numbers and send SMS to each
    for phone_number in settings.ADMIN_PHONE_NUMBERS:
        if send_sms_notification(phone_number, sms_body):
            sent_any_successfully = True
        else:
            logger.error(f"Individual SMS failed to send to admin {phone_number} for new user {user.username}.")

    if sent_any_successfully:
        logger.info(f"Admin SMS notification process completed for new user: {user.username}.")
    else:
        logger.error(f"No admin SMS notifications could be sent for new user: {user.username}.")

    return sent_any_successfully