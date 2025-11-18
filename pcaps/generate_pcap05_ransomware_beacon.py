#!/usr/bin/env python3
from scapy.all import IP, UDP, Raw, wrpcap

def generate_ransom_beacons(output_file: str = "pcap05_ransomware_beacon.pcap"):
    pkts = []
    infected_ip = "10.77.8.20"
    c2_ip = "103.22.144.9"

    for i in range(10):
        load = f"ENC_BEACON_{i}".encode()
        pkt = IP(src=infected_ip, dst=c2_ip) / UDP(
            dport=4444,
            sport=55000 + i
        ) / Raw(load=load)
        pkt.time = i * 30
        pkts.append(pkt)

    wrpcap(output_file, pkts)
    print(f"[+] Wrote {len(pkts)} packets to {output_file}")

if __name__ == "__main__":
    generate_ransom_beacons()
