from pprint import pprint

import requests
from django.conf import settings


class experttexting_sms:

    def __init__(self, to, message) -> None:
        self.base_url_SendSMS = (
            'https://www.experttexting.com/ExptRestApi/sms/json/Message/Send'
        )
        self.base_url_QueryBalance = (
            'https://www.experttexting.com/ExptRestApi/sms/json/Account/Balance'
        )

        self.username = getattr(settings, 'TEXT_EXPERT_USERNAME', '')
        self.password = getattr(settings, 'TEXT_EXPERT_PASSWORD', '')
        self.apikey = getattr(settings, 'TEXT_EXPERT_API_KEY', '')
        self.fromwho = 'DEFAULT'

        # Clean destination phone number: ExpertTexting requires no '+' or spaces
        self.to = str(to).replace('+', '').replace(' ', '')
        self.msgtext = message

    def send(self) -> bool:
        payload = {
            'username': self.username,
            'password': self.password,
            'api_key': self.apikey,
            'FROM': self.fromwho,
            'to': self.to,
            'text': self.msgtext,
        }

        try:
            r = requests.post(self.base_url_SendSMS, data=payload, timeout=10)

            # Safely check HTTP Status
            if r.status_code != 200:
                print(
                    f'[SMS Gateway Error] HTTP {r.status_code}: {r.text}'
                )
                return False

            # Try parsing JSON safely
            data = r.json()
            pprint(data)

            # ExpertTexting usually returns ResponseCode 0 or Status 200 on success
            if data.get('ResponseCode') == '0' or data.get('Status') == 200:
                return True

            print(f"[SMS Gateway Failed] Response: {data}")
            return False

        except requests.exceptions.JSONDecodeError:
            print(f"[SMS Gateway Raw Response (Not JSON)]: {r.text}")
            return False
        except Exception as e:
            print(f"[SMS Gateway Exception]: {e!s}")
            return False