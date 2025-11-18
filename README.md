# CIT 480 – Operation Nightingale Cyber Range

This repository contains simulation-ready artifacts and automation for the
**Operation Nightingale** cyber range used in:

> **CIT 480 – Advanced Topics in Cybersecurity**

It is designed for teaching:

- Global incident response
- Healthcare and critical infrastructure security
- Cloud, IoT, OT, and supply-chain security
- Threat intelligence and deepfake/disinformation analysis

All artifacts are **safe**, non-malicious, and intended for educational use only.

## Components

- `build_cit480_topology.py`  
  Python script that connects to one or more GNS3 servers and programmatically
  builds the Operation Nightingale topology (routers, switches, VMs, links),
  sets nodes to autostart, and pushes sample IOS configs (with OSPF + DHCP).

- `scripts/install_splunk_siem.sh`  
  Non-interactive native Splunk install script for the SOC SIEM VM
  (`soc-siem-01`), intended to be triggered by Jenkins.

- `Jenkinsfile`  
  Jenkins pipeline that:
  1. Runs the GNS3 topology builder.
  2. SSHes into the SIEM VM and installs + starts Splunk.

- `pcaps/`  
  Scapy-based Python scripts that generate **synthetic PCAPs** used in labs:
  early C2 beaconing, RDP brute force, MQTT IoT attacks, supply-chain beacons,
  ransomware beacons, and Modbus/OT writes.

- `logs/`  
  Sample logs for selected labs (firewall, VPN, AD, MQTT, ransomware, registry).

- `artifacts/`  
  A fictional SparrowCrypt ransomware note (HTML) for ransom analysis labs.

- `deepfake/`  
  Fake CEO transcript, attacker storyboard, and phishing email headers
  for the deepfake / disinformation lab.

## GNS3 Topology (High Level)

The topology includes:

- **core-rtr** ↔ “internet” cloud
- **US site**: `us-edge`, `us-sw`, `us-ehr-01`, `us-iot-gw-01`, `us-ad-01`
- **UK site**: `uk-edge`, `uk-sw`, `uk-img-01`, `uk-ehr-01`
- **Singapore site**: `sg-edge`, `sg-sw`, `sg-web-01`, `sg-db-01`
- **SOC**: `soc-rtr`, `soc-sw`, `soc-siem-01` (Ubuntu + Splunk), `soc-analyst-01`
- **Cloud**: `cloud-rtr`, `cloud-sw`, `cloud-web-01`, `cloud-api-01`
- **OT/ICS**: `ot-rtr`, `ot-sw`, `plc-sim-01`, `bms-01`

Routing uses **OSPF 1**, and edge routers provide **DHCP** for local LANs so
hosts can obtain IP addresses automatically.

## Requirements

- Python 3.8+  
- GNS3 server(s) reachable at `http://10.48.229.X:80` (configurable via `datastore`)  
- GNS3 templates matching the names in `build_cit480_topology.py`:
  - `Cisco IOSv 15.5(3)M`
  - `Cisco IOSvL2 15.2.1`
  - `Windows 10 w/ Edge`
  - `Windows Server 2022`
  - `Ubuntu Server 22.04`
  - `Cloud`

Install Python dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Using the GNS3 builder

1. Create a `datastore` file in the repo root containing **last octets** of your
   GNS3 servers, comma-separated. Example for `10.48.229.245`:

   ```text
   245
   ```

2. Run:

```bash
python3 build_cit480_topology.py
```

3. The script will:
   - Connect to each GNS3 server,
   - Create the project `cit480-operation-nightingale`,
   - Create all nodes and links,
   - Set nodes to autostart and start them,
   - Push IOS configs to routers (OSPF + DHCP).

## Jenkins + Splunk

The included `Jenkinsfile` assumes:

- `build_cit480_topology.py` is in the repo root.
- A Jenkins credential `siem-ubuntu-creds` exists with SSH username/password
  for the `soc-siem-01` Ubuntu template.
- `soc-siem-01` has a **static IP** of `10.99.10.20`.
- Jenkins agent has `sshpass` installed.

Pipeline stages:

1. **Build GNS3 Topology** – runs the builder script.
2. **Install & Start Splunk on SIEM** – copies and executes
   `scripts/install_splunk_siem.sh` on `soc-siem-01` to install native Splunk.

## PCAPs

From `pcaps/`, run:

```bash
cd pcaps
python3 generate_pcap01_early_warning.py
python3 generate_pcap02_identity_anomalies.py
python3 generate_pcap03_medical_iot.py
python3 generate_pcap04_supply_chain.py
python3 generate_pcap05_ransomware_beacon.py
python3 generate_pcap11_modbus_attack.py
```

Each script produces a `.pcap` file in the same directory for use in labs.

## Safety Notice

- No real malware or exploit code is included.
- PCAPs contain synthetic, harmless traffic patterns.
- Ransomware notes and deepfake artifacts are fictional and for analysis only.
