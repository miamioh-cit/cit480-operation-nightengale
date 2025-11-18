#!/usr/bin/env python3
from scapy.all import IP, TCP, Raw, wrpcap

def generate_mqtt_attack(output_file: str = "pcap03_medical_iot.pcap"):
    packets = []
    attacker = "10.50.1.99"
    broker = "10.50.1.10"
    topic = "devices/pump/control/override"
    template = "PUBLISH {} dose=+2.0"

    for i in range(5):
        load = template.format(topic).encode()
        pkt = IP(src=attacker, dst=broker) / TCP(
            dport=1883,
            sport=40000 + i,
            flags="PA"
        ) / Raw(load=load)
        pkt.time = i * 5
        packets.append(pkt)

    wrpcap(output_file, packets)
    print(f"[+] Wrote {len(packets)} packets to {output_file}")

if __name__ == "__main__":
    generate_mqtt_attack()
