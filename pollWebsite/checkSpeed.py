import speedtest

def run_speed_test():
    print("Running speed test... Please wait.\n")
    print("This will take a while, please wait.\n")
    
    st = speedtest.Speedtest()
    
    # Get the best server based on ping
    st.get_best_server()
    
    # Run tests
    download_speed = st.download() / 1_000_000   # Convert to Mbps
    upload_speed = st.upload() / 1_000_000       # Convert to Mbps
    ping = st.results.ping
    
    # Display results
    print("=== Speed Test Results ===")
    print(f"Ping: {ping:.2f} ms")
    print(f"Download: {download_speed:.2f} Mbps")
    print(f"Upload: {upload_speed:.2f} Mbps")

if __name__ == "__main__":
    run_speed_test()
