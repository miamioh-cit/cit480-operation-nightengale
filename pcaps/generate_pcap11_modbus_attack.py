#!/usr/bin/env python3
from scapy.all import IP, TCP, Raw, wrpcap

def generate_modbus(output_file: str = "pcap11_modbus_attack.pcap"):
    pkts = []
    attacker = "10.60.1.50"
    plc = "10.60.1.10"
    payload = b"\x01\x06\x9C\xB9\x00\x00"

    for i in range(3):
        pkt = IP(src=attacker, dst=plc) / TCP(
            dport=502,
            sport=51000 + i,
            flags="PA"
        ) / Raw(load=payload)
        pkt.time = i * 3
        pkts.append(pkt)

    wrpcap(output_file, pkts)
    print(f"[+] Wrote {len(pkts)} packets to {output_file}")

if __name__ == "__main__":
    generate_modbus()
