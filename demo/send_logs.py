import socket
import time

# Configuration
LOGSTASH_HOST = '192.168.31.62'
LOGSTASH_PORT = 1701

# The raw log string
log_message_1 = "2025-12-06T14:52:33Z host-7fa3 kernel[1324]: Unauthorized access attempt detected from 192.168.70.51 on port 445 (rule_id=WIN-SMB-401, severity=medium)"
log_message_2 = '''<Event xmlns='http://schemas.microsoft.com/win/2004/08/events/event'><System><Provider Name='Microsoft-Windows-SystemDataArchiver' Guid='{4389f802-0c4f-56d0-63c6-d77db206d237}'/><EventID>2050</EventID><Version>0</Version><Level>4</Level><Task>0</Task><Opcode>0</Opcode><Keywords>0x8000000000000000</Keywords><TimeCreated SystemTime='2026-01-03T03:11:00.009253100Z'/><EventRecordID>74472465</EventRecordID><Correlation ActivityID='{7bd59d8c-9e2c-4901-bde8-075167a21295}'/><Execution ProcessID='4524' ThreadID='5100'/><Channel>Microsoft-Windows-SystemDataArchiver/Diagnostic</Channel><Computer>CyberLab-ICA001.stecyberlab.local</Computer><Security UserID='S-1-5-19'/></System><EventData><Data Name='LogString'>[SDP Base]  SRUM calling QueryStatsEx with reason 0 into provider Network Provider.</Data></EventData></Event>'''
log_message_3 = '''<Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event"><System><Provider Name="Microsoft-Windows-PowerShell" Guid="{A0C1853B-5C40-4B15-8766-3CF1C58F985A}" /><EventID>4103</EventID><Version>1</Version><Level>3</Level><Task>2</Task><Opcode>15</Opcode><Keywords>0x0</Keywords><TimeCreated SystemTime="2026-01-04T12:00:00.0000000Z" /><EventRecordID>4521</EventRecordID><Correlation ActivityID="{84206580-B753-0002-3084-218453B7D901}" /><Execution ProcessID="6420" ThreadID="5812" /><Channel>Microsoft-Windows-PowerShell/Operational</Channel><Computer>FS03.offsec.lan</Computer><Security UserID="S-1-5-21-4230534742-2542757381-3142984815-1111" /></System><EventData><Data Name="MessageNumber">1</Data><Data Name="MessageTotal">1</Data><Data Name="Payload">Get-NetFirewallRule</Data> <Data Name="ScriptBlockId">38260b09-201a-4286-81c4-112233445566</Data><Data Name="Path"></Data></EventData></Event>'''

def send_log():
    try:
        # Create a TCP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5) 
        
        # Connect to Logstash
        sock.connect((LOGSTASH_HOST, LOGSTASH_PORT))
        
        # payload = log_message_1
        # sock.sendall(payload.encode('utf-8'))
        # print(f"Log sent to {LOGSTASH_HOST}:{LOGSTASH_PORT}")
        
        # time.sleep(10)
        # payload = log_message_2
        # sock.sendall(payload.encode('utf-8'))
        # print(f"Log sent to {LOGSTASH_HOST}:{LOGSTASH_PORT}")

        payload = log_message_3
        sock.sendall(payload.encode('utf-8'))
        print(f"Log sent to {LOGSTASH_HOST}:{LOGSTASH_PORT}")

    except ConnectionRefusedError:
        print(f"Connection refused: Is Logstash running on {LOGSTASH_HOST}?")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # CLOSE the socket. This tells Logstash "The event is finished."
        sock.close()
    
    time.sleep(60)

if __name__ == "__main__":
    print("Starting plain text log sender...")
    while True:
        send_log()