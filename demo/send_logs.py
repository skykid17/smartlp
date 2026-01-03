import socket
import time

# Configuration
LOGSTASH_HOST = '192.168.31.62'
LOGSTASH_PORT = 1701

# The raw log string
log_message_1 = "2025-12-06T14:52:33Z host-7fa3 kernel[1324]: Unauthorized access attempt detected from 192.168.70.51 on port 445 (rule_id=WIN-SMB-401, severity=medium)"
log_message_2 = '''<Event xmlns='http://schemas.microsoft.com/win/2004/08/events/event'><System><Provider Name='Microsoft-Windows-SystemDataArchiver' Guid='{4389f802-0c4f-56d0-63c6-d77db206d237}'/><EventID>2050</EventID><Version>0</Version><Level>4</Level><Task>0</Task><Opcode>0</Opcode><Keywords>0x8000000000000000</Keywords><TimeCreated SystemTime='2026-01-03T03:11:00.009253100Z'/><EventRecordID>74472465</EventRecordID><Correlation ActivityID='{7bd59d8c-9e2c-4901-bde8-075167a21295}'/><Execution ProcessID='4524' ThreadID='5100'/><Channel>Microsoft-Windows-SystemDataArchiver/Diagnostic</Channel><Computer>CyberLab-ICA001.stecyberlab.local</Computer><Security UserID='S-1-5-19'/></System><EventData><Data Name='LogString'>[SDP Base]  SRUM calling QueryStatsEx with reason 0 into provider Network Provider.</Data></EventData></Event>'''
def send_log():
    try:
        # Create a TCP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5) 
        
        # Connect to Logstash
        sock.connect((LOGSTASH_HOST, LOGSTASH_PORT))
        
        payload = log_message_1 + '\n'
        sock.sendall(payload.encode('utf-8'))
        
        print(f"Log sent to {LOGSTASH_HOST}:{LOGSTASH_PORT}")
        time.sleep(10)
        payload = log_message_2 + '\n'
        sock.sendall(payload.encode('utf-8'))

    except ConnectionRefusedError:
        print(f"Connection refused: Is Logstash running on {LOGSTASH_HOST}?")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # CLOSE the socket. This tells Logstash "The event is finished."
        sock.close()
    
    time.sleep(10)

if __name__ == "__main__":
    print("Starting plain text log sender...")
    while True:
        send_log()