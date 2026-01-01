import socket
import time

# Configuration
LOGSTASH_HOST = '192.168.31.62'
LOGSTASH_PORT = 1701

# The raw log string
raw_log_message = "2025-12-06T14:52:33Z host-7fa3 kernel[1324]: Unauthorized access attempt detected from 192.168.70.51 on port 445 (rule_id=WIN-SMB-401, severity=medium)"

def send_log():
    try:
        # Create a TCP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5) 
        
        # Connect to Logstash
        sock.connect((LOGSTASH_HOST, LOGSTASH_PORT))
        
        payload = raw_log_message + '\n'
        sock.sendall(payload.encode('utf-8'))
        
        print(f"Log sent to {LOGSTASH_HOST}:{LOGSTASH_PORT}")
        
    except ConnectionRefusedError:
        print(f"Connection refused: Is Logstash running on {LOGSTASH_HOST}?")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # CLOSE the socket. This tells Logstash "The event is finished."
        sock.close()

if __name__ == "__main__":
    print("Starting plain text log sender...")
    while True:
        send_log()
        time.sleep(60)