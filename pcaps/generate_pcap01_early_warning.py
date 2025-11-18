#!/usr/bin/env python3
from scapy.all import IP, TCP, wrpcap
import random

def generate_beacons(output_file: str = "pcap01_early_warning.pcap"):
    packets = []
    c2_ip = "185.198.57.14"
    internal_ip = "10.4.22.12"

    for t in range(0, 600, 60):
        pkt = IP(src=internal_ip, dst=c2_ip) / TCP(
            dport=443,
            sport=50000 + random.randint(1, 1000),
            flags="S"
        )
        pkt.time = t
        packets.append(pkt)

    wrpcap(output_file, packets)
    print(f"[+] Wrote {len(packets)} packets to {output_file}")

if __name__ == "__main__":
    generate_beacons()
