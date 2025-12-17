import argparse
import requests
import time

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning) 

parser = argparse.ArgumentParser(description='Poll a URL periodically')
parser.add_argument('-i', '--input-url', default="https://aptserver.csez.zohocorpin.com/", help='The URL to poll')
parser.add_argument('-f', '--polling-freq', type=int, default=3, help='Polling frequency in minutes (default: 3)')
args = parser.parse_args()
url = args.input_url
poll_freq_in_minutes = args.polling_freq

def main():
    while True:
        print(f"100: Polling every {poll_freq_in_minutes} minutes")
        try:
            print(f"200: {time.ctime()} :: POLLING: {url}")
            r = requests.get(url, verify=False)
            if r.status_code == 200:
                print(f"200: {time.ctime()} :: Reached Website Successfully...")
            else:
                print(f"{r.status_code}: {time.ctime()} :: STATUS_CODE: {r.status_code}")
        except Exception as e:
            print(f"500: {time.ctime()} :: Exception occurred: {e}")
        finally:
            print("999: ---------------------------------")
            time.sleep(poll_freq_in_minutes * 60)

if __name__ == "__main__":
    main()
