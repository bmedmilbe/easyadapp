from requests.exceptions import RequestException

from .expt import experttexting_sms


def send_pin_sms(mobile_number, pin):
    """
    Centralized helper function to send PIN via SMS.
    Returns True if successful, False otherwise.
    """
    try:
        print(f"[SMS] Sending PIN {pin} to {mobile_number}")
        message = f"Oi! Use o PIN {pin} para entrar no feladoxi.vercel.app"

        expert_sms = experttexting_sms(to=str(mobile_number), message=message)
        expert_sms.send()

        return True
    except RequestException as e:
        print(f"[SMS ERROR] Failed to send PIN to {mobile_number}: {e!s}")
        return False
