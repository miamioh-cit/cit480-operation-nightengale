#!/usr/bin/env python3
from scapy.all import IP, TCP, wrpcap

def generate_login_attempts(output_file: str = "pcap02_identity_anomalies.pcap"):
    packets = []
    attacker_ip = "201.57.22.94"
    target_ip = "10.22.5.20"

    for i in range(20):
        pkt = IP(src=attacker_ip, dst=target_ip) / TCP(dport=3389, flags="S")
        pkt.time = i * 2
        packets.append(pkt)

    success = IP(src=attacker_ip, dst=target_ip) / TCP(dport=3389, flags="PA")
    success.time = 45
    packets.append(success)

    wrpcap(output_file, packets)
    print(f"[+] Wrote {len(packets)} packets to {output_file}")

if __name__ == "__main__":
    generate_login_attempts()
