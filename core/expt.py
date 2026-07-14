import requests
from pprint import pprint

from django.conf import settings
class experttexting_sms():
  
  def __init__(self, to, message) -> None:
     

	# // Base URLS for three methods
    self.base_url_SendSMS = 'https://www.experttexting.com/ExptRestApi/sms/json/Message/Send'
    self.base_url_QueryBalance = 'https://www.experttexting.com/ExptRestApi/sms/json/Account/Balance?'
    
	# // Public Variables that are used as parameters in API calls
    self.username = settings.TEXT_EXPERT_USERNAME 
    self.password = settings.TEXT_EXPERT_PASSWORD
    self.apikey = settings.TEXT_EXPERT_API_KEY
    self.fromwho = 'DEFAULT'	
    # // USE DEFAULT IN MOST CASES, CONTACT SUPPORT FOR FURTHER DETAILS>
    self.to = to		
    # // LET THIS REMAIN BLANK
    self.msgtext = message	
    # // LET THIS REMAIN BLANK
    
  def send(self):
        # fieldcnt    = 6
        # fieldstring = f"username={}&password={}&api_key={}&FROM={}&to={}&text={}"
      
        payload = {
           "username":settings.TEXT_EXPERT_USERNAME,
           "password":settings.TEXT_EXPERT_PASSWORD,
           "api_key":settings.TEXT_EXPERT_API_KEY,
           "FROM":"DEFAULT", 
           "to":self.to,
           "text":self.msgtext
        }
        pprint(payload)
        
       

        url = self.base_url_SendSMS
        pprint(url)
        # headers = {'content-type': 'application/json', 'Accept-Charset': 'UTF-8'}
        r = requests.post(url, data=payload)
        pprint(r.json())
    
    
  # // SEND SMS FUNCTION FOR UNICODE TEXT
  def sendUnicode(self):
    
        fieldcnt    = 6
        fieldstring = f"username={self.username}&password={self.password}&api_key={self.api_key}&FROM={self.fromwho}&to={self.to}&text={self.msgtext}&type={self.unicode}"
        
        # $ch = curl_init()
        # curl_setopt($ch, CURLOPT_URL, $this->base_url_SendSMSUnicode)
        # curl_setopt($ch, CURLOPT_POST, $fieldcnt)
        # curl_setopt($ch, CURLOPT_POSTFIELDS, $fieldstring)
        # curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false)
        # curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1)
        # $res = curl_exec($ch)
        # $err = curl_error($ch)
        # curl_close($ch)
        # if ($err) {
        #   echo "cURL Error #:" . $err
        # } else {
        #   echo $res
        # }
    
    
    # // FUNCTION TO QUERY YOUR ACCOUNT BALANC
  def QueryBalance(self):
    
        
        fieldstring = f"username={self.username}&password={self.password}&api_key={self.apikey}"
        
        # $curl = curl_init()

        # curl_setopt_array($curl, array(
        #   CURLOPT_URL =>  $this->base_url_QueryBalance . $fieldstring ,
        #   CURLOPT_RETURNTRANSFER => true,
        #   CURLOPT_ENCODING => "",
        #   CURLOPT_MAXREDIRS => 10,
        #   CURLOPT_TIMEOUT => 30,
        #   CURLOPT_SSL_VERIFYPEER => false,
        #   CURLOPT_HTTP_VERSION => CURL_HTTP_VERSION_1_1,
        #   CURLOPT_CUSTOMREQUEST => "GET"
        # ))

        # $response = curl_exec($curl)
        # $err = curl_error($curl)

        # curl_close($curl)

        # if ($err) {
        #   echo "cURL Error #:" . $err
        # } else {
        #   echo $response
        # }
   
# expert = experttexting_sms()
# expert.send()