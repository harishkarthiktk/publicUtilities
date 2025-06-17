import requests

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning) 

import time 
url = "https://udyamregistration.gov.in/"
poll_freq_in_minutes = 15

while True:
    print(f"Polling every {poll_freq_in_minutes} minutes")
    try:
        print(f"{time.ctime()} :: POLLING: {url}")
        r = requests.get(url, verify=False)
        if r.status_code == 200:
            print("{time.ctime()} :: Reached Website Successfully...")
        else:
            print(f"{time.ctime()} :: STATUS_CODE: {r.status_code}")
    except Exception as e:
        print(f"{time.ctime()} :: Exception occurred: {e}")
    finally:
        print("---------------------------------")
        time.sleep(poll_freq_in_minutes * 60)