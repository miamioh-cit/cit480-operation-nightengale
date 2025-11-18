#!/usr/bin/env python3
from scapy.all import IP, TCP, Raw, wrpcap

def generate_supply_chain(output_file: str = "pcap04_supply_chain.pcap"):
    pkts = []
    src_ip = "10.33.4.12"
    dst_ip = "91.212.150.43"

    for i in range(5):
        load = f"POST /checkin HTTP/1.1\r\nHost: {dst_ip}\r\n\r\n".encode()
        pkt = IP(src=src_ip, dst=dst_ip) / TCP(
            dport=80,
            sport=45000 + i,
            flags="PA"
        ) / Raw(load=load)
        pkt.time = i * 10
        pkts.append(pkt)

    wrpcap(output_file, pkts)
    print(f"[+] Wrote {len(pkts)} packets to {output_file}")

if __name__ == "__main__":
    generate_supply_chain()
