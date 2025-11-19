import logging
import os
import subprocess
from pathlib import Path

from gns3fy import Gns3Connector, Project

# -------------------------------------------------------------------
# Lab name and GNS3 server configuration
# -------------------------------------------------------------------

DEFAULT_LAB_NAME = "cit480-operation-nightingale"
# Jenkins will set LAB_NAME in the environment, e.g. cit480-operation-nightingale-42
LAB_NAME = os.getenv("LAB_NAME", DEFAULT_LAB_NAME)

BASE_IP = "http://10.48.229."

# Where per-node cloud-init YAML + ISO files will be written.
# Make sure this path is accessible to your GNS3 server.
CLOUD_INIT_DIR = Path(os.getenv("CLOUD_INIT_DIR", "/opt/gns3/images/cloud-init"))

# Read last octets from datastore file
try:
    with open("datastore", "r") as f:
        content = f.read().strip()
        SERVER_LAST_OCTETS = [
            int(octet.strip())
            for octet in content.split(",")
            if octet.strip().isdigit()
        ]
except Exception as e:
    print("Error reading datastore file:", e)
    SERVER_LAST_OCTETS = []

if not SERVER_LAST_OCTETS:
    raise ValueError("No valid server last octets found in 'datastore'.")

SERVER_URLS = [f"{BASE_IP}{octet}:80" for octet in SERVER_LAST_OCTETS]

GNS3_USER = "gns3"
GNS3_PW = "gns3"

# Template names (adjust to match your GNS3 server)
TEMPLATE_IOSV = "Cisco IOSv 15.5(3)M"
TEMPLATE_IOSVL2 = "Cisco IOSvL2 15.2.1"
TEMPLATE_WIN10 = "Windows 10 w/ Edge"
TEMPLATE_WINSRV = "Windows Server 2022"
TEMPLATE_UBUNTU = "Ubuntu Server 22.04"
TEMPLATE_CLOUD = "Cloud"

# -------------------------------------------------------------------
# Cloud-init template (per-node)
# -------------------------------------------------------------------

CLOUD_INIT_TEMPLATE = """#cloud-config
hostname: {hostname}
preserve_hostname: false

users:
  - name: student
    gecos: Student User
    sudo: ALL=(ALL) NOPASSWD:ALL
    groups: sudo
    ssh_pwauth: true
    lock_passwd: false
    passwd: "$6$uEQ69TUW0/3k4zzA$92HhrfEmUKq7WPG3Y2vFpLUuJoOPzjF7J7T0BwWmqugGSk8iJIGv9STtgdXGx0AYCEhduQuFRhRFKCvuYqaOz/"

package_update: true
package_upgrade: true

packages:
  - python3
  - python3-pip
  - net-tools
  - curl
  - unzip
  - jq
  - wget
  - gnupg
  - systemd-timesyncd

write_files:
  - path: /etc/motd
    content: |
      Welcome to the CIT 480 Cyber Range
      Auto-provisioned via cloud-init for {hostname}

runcmd:
  - systemctl enable ssh
  - systemctl start ssh
  - timedatectl set-timezone America/New_York
  - echo "CIT480 provisioning complete on {hostname}." > /var/log/cit480-provision.log
"""

# Ubuntu nodes in this topology that should get cloud-init
UBUNTU_NODES = [
    "soc-siem-01",
    "cloud-web-01",
    "cloud-api-01",
    "plc-sim-01",
    "us-iot-gw-01",
    "uk-ehr-01",
    "sg-web-01",
    "sg-db-01",
]


def ensure_cloud_init_iso(hostname: str) -> Path:
    """
    Generate a per-node cloud-init YAML + seed ISO using cloud-localds.

    YAML: <CLOUD_INIT_DIR>/<hostname>-cloudinit.yaml
    ISO:  <CLOUD_INIT_DIR>/<hostname>-seed.iso

    Returns the ISO path (even if cloud-localds is missing, so you can
    see where it *would* be).
    """
    CLOUD_INIT_DIR.mkdir(parents=True, exist_ok=True)

    yaml_path = CLOUD_INIT_DIR / f"{hostname}-cloudinit.yaml"
    iso_path = CLOUD_INIT_DIR / f"{hostname}-seed.iso"

    yaml_content = CLOUD_INIT_TEMPLATE.format(hostname=hostname)
    yaml_path.write_text(yaml_content, encoding="utf-8")
    print(f"[+] Wrote cloud-init YAML for {hostname} to {yaml_path}")

    # Try to build the ISO via cloud-localds
    try:
        subprocess.run(
            ["cloud-localds", str(iso_path), str(yaml_path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        print(f"[+] Created cloud-init seed ISO for {hostname} at {iso_path}")
    except FileNotFoundError:
        print(
            f"[!] cloud-localds not found. Install 'cloud-image-utils' on this host "
            f"to auto-generate cloud-init ISOs. YAML still written at {yaml_path}."
        )
    except subprocess.CalledProcessError as e:
        print(
            f"[!] Error running cloud-localds for {hostname}: {e}. "
            f"YAML is at {yaml_path}, you can build the ISO manually."
        )

    return iso_path

# -------------------------------------------------------------------
# IOS router configs with IPs + OSPF + DHCP
# -------------------------------------------------------------------

ROUTER_CONFIGS = {
    "core-rtr": """
hostname core-rtr
no ip domain-lookup
!
interface GigabitEthernet0/0
 description TO-INTERNET
 ip address 10.0.0.1 255.255.255.252
 no shutdown
!
interface GigabitEthernet0/1
 description TO-US-EDGE
 ip address 10.10.0.1 255.255.255.252
 no shutdown
!
interface GigabitEthernet0/2
 description TO-UK-EDGE
 ip address 10.20.0.1 255.255.255.252
 no shutdown
!
interface GigabitEthernet0/3
 description TO-SG-EDGE
 ip address 10.30.0.1 255.255.255.252
 no shutdown
!
interface GigabitEthernet0/4
 description TO-CLOUD-RTR
 ip address 10.200.0.1 255.255.255.252
 no shutdown
!
interface GigabitEthernet0/5
 description TO-SOC-RTR
 ip address 10.99.0.1 255.255.255.252
 no shutdown
!
interface GigabitEthernet0/6
 description TO-OT-RTR
 ip address 10.60.0.1 255.255.255.252
 no shutdown
!
router ospf 1
 router-id 1.1.1.1
 network 10.0.0.0 0.0.0.3 area 0
 network 10.10.0.0 0.0.0.3 area 0
 network 10.20.0.0 0.0.0.3 area 0
 network 10.30.0.0 0.0.0.3 area 0
 network 10.60.0.0 0.0.0.3 area 0
 network 10.99.0.0 0.0.0.3 area 0
 network 10.200.0.0 0.0.0.3 area 0
!
ip route 0.0.0.0 0.0.0.0 10.0.0.2
!
line vty 0 4
 login local
 transport input ssh
!
end
""",
    "us-edge": """
hostname us-edge
no ip domain-lookup
!
interface GigabitEthernet0/0
 description TO-CORE
 ip address 10.10.0.2 255.255.255.252
 no shutdown
!
interface GigabitEthernet0/1
 description TO-US-SW
 ip address 10.10.10.1 255.255.255.0
 no shutdown
!
ip dhcp excluded-address 10.10.10.1 10.10.10.19
ip dhcp pool US-LAN
 network 10.10.10.0 255.255.255.0
 default-router 10.10.10.1
 dns-server 10.10.10.1
!
router ospf 1
 router-id 2.2.2.2
 network 10.10.0.0 0.0.0.3 area 0
 network 10.10.10.0 0.0.0.255 area 0
!
ip route 0.0.0.0 0.0.0.0 10.10.0.1
!
line vty 0 4
 login local
 transport input ssh
!
end
""",
    "uk-edge": """
hostname uk-edge
no ip domain-lookup
!
interface GigabitEthernet0/0
 description TO-CORE
 ip address 10.20.0.2 255.255.255.252
 no shutdown
!
interface GigabitEthernet0/1
 description TO-UK-SW
 ip address 10.20.10.1 255.255.255.0
 no shutdown
!
ip dhcp excluded-address 10.20.10.1 10.20.10.19
ip dhcp pool UK-LAN
 network 10.20.10.0 255.255.255.0
 default-router 10.20.10.1
 dns-server 10.20.10.1
!
router ospf 1
 router-id 3.3.3.3
 network 10.20.0.0 0.0.0.3 area 0
 network 10.20.10.0 0.0.0.255 area 0
!
ip route 0.0.0.0 0.0.0.0 10.20.0.1
!
line vty 0 4
 login local
 transport input ssh
!
end
""",
    "sg-edge": """
hostname sg-edge
no ip domain-lookup
!
interface GigabitEthernet0/0
 description TO-CORE
 ip address 10.30.0.2 255.255.255.252
 no shutdown
!
interface GigabitEthernet0/1
 description TO-SG-SW
 ip address 10.30.10.1 255.255.255.0
 no shutdown
!
ip dhcp excluded-address 10.30.10.1 10.30.10.19
ip dhcp pool SG-LAN
 network 10.30.10.0 255.255.255.0
 default-router 10.30.10.1
 dns-server 10.30.10.1
!
router ospf 1
 router-id 4.4.4.4
 network 10.30.0.0 0.0.0.3 area 0
 network 10.30.10.0 0.0.0.255 area 0
!
ip route 0.0.0.0 0.0.0.0 10.30.0.1
!
line vty 0 4
 login local
 transport input ssh
!
end
""",
    "cloud-rtr": """
hostname cloud-rtr
no ip domain-lookup
!
interface GigabitEthernet0/0
 description TO-CORE
 ip address 10.200.0.2 255.255.255.252
 no shutdown
!
interface GigabitEthernet0/1
 description TO-CLOUD-SW
 ip address 10.200.10.1 255.255.255.0
 no shutdown
!
ip dhcp excluded-address 10.200.10.1 10.200.10.19
ip dhcp pool CLOUD-LAN
 network 10.200.10.0 255.255.255.0
 default-router 10.200.10.1
 dns-server 10.200.10.1
!
router ospf 1
 router-id 5.5.5.5
 network 10.200.0.0 0.0.0.3 area 0
 network 10.200.10.0 0.0.0.255 area 0
!
ip route 0.0.0.0 0.0.0.0 10.200.0.1
!
line vty 0 4
 login local
 transport input ssh
!
end
""",
    "soc-rtr": """
hostname soc-rtr
no ip domain-lookup
!
interface GigabitEthernet0/0
 description TO-CORE
 ip address 10.99.0.2 255.255.255.252
 no shutdown
!
interface GigabitEthernet0/1
 description TO-SOC-SW
 ip address 10.99.10.1 255.255.255.0
 no shutdown
!
ip dhcp excluded-address 10.99.10.1 10.99.10.19
ip dhcp pool SOC-LAN
 network 10.99.10.0 255.255.255.0
 default-router 10.99.10.1
 dns-server 10.99.10.1
!
router ospf 1
 router-id 6.6.6.6
 network 10.99.0.0 0.0.0.3 area 0
 network 10.99.10.0 0.0.0.255 area 0
!
ip route 0.0.0.0 0.0.0.0 10.99.0.1
!
line vty 0 4
 login local
 transport input ssh
!
end
""",
    "ot-rtr": """
hostname ot-rtr
no ip domain-lookup
!
interface GigabitEthernet0/0
 description TO-CORE
 ip address 10.60.0.2 255.255.255.252
 no shutdown
!
interface GigabitEthernet0/1
 description TO-OT-SW
 ip address 10.60.1.1 255.255.255.0
 no shutdown
!
ip dhcp excluded-address 10.60.1.1 10.60.1.19
ip dhcp pool OT-LAN
 network 10.60.1.0 255.255.255.0
 default-router 10.60.1.1
 dns-server 10.60.1.1
!
router ospf 1
 router-id 7.7.7.7
 network 10.60.0.0 0.0.0.3 area 0
 network 10.60.1.0 0.0.0.255 area 0
!
ip route 0.0.0.0 0.0.0.0 10.60.0.1
!
line vty 0 4
 login local
 transport input ssh
!
end
"""
}

# -------------------------------------------------------------------
# Helper to apply configs
# -------------------------------------------------------------------

def apply_router_configs(lab: Project):
    for router_name, cfg in ROUTER_CONFIGS.items():
        try:
            node = lab.get_node(router_name)
            node.get()
            node.update(config=cfg)
            print(f"[+] Applied config to {router_name}")
        except Exception as e:
            print(f"[!] Failed to apply config to {router_name}: {e}")

# -------------------------------------------------------------------
# Main project creation loop
# -------------------------------------------------------------------

for SERVER_URL in SERVER_URLS:
    server = Gns3Connector(url=SERVER_URL, user=GNS3_USER, cred=GNS3_PW)
    print(f"Connecting to GNS3 server {SERVER_URL}, version: {server.get_version()}")
    print(f"[*] Using LAB_NAME = {LAB_NAME}")

    server.create_project(name=LAB_NAME)
    print(f"Project '{LAB_NAME}' created on {SERVER_URL}")

    lab = Project(name=LAB_NAME, connector=server)
    lab.get()
    lab.open()

    available_templates = [template["name"] for template in server.get_templates()]
    logging.debug(f"Available Templates: {available_templates}")

    # Generate per-node cloud-init artifacts for all Ubuntu nodes
    print("[*] Generating per-node cloud-init YAML + ISOs for Ubuntu nodes...")
    for ubuntu_host in UBUNTU_NODES:
        ensure_cloud_init_iso(ubuntu_host)
    print("[*] Cloud-init generation step completed.")

    # ----------------------------------------------------------------
    # CORE / INTERNET / SOC / CLOUD / OT
    # ----------------------------------------------------------------
    lab.create_node(name="internet", template=TEMPLATE_CLOUD, x=-200, y=-200)

    lab.create_node(name="core-rtr", template=TEMPLATE_IOSV, x=-50, y=-200)
    lab.create_node(name="soc-rtr", template=TEMPLATE_IOSV, x=200, y=-200)
    lab.create_node(name="soc-sw", template=TEMPLATE_IOSVL2, x=200, y=-100)
    lab.create_node(name="soc-siem-01", template=TEMPLATE_UBUNTU, x=350, y=-100)
    lab.create_node(name="soc-analyst-01", template=TEMPLATE_WIN10, x=350, y=-10)

    lab.create_node(name="cloud-rtr", template=TEMPLATE_IOSV, x=-50, y=0)
    lab.create_node(name="cloud-sw", template=TEMPLATE_IOSVL2, x=-50, y=100)
    lab.create_node(name="cloud-web-01", template=TEMPLATE_UBUNTU, x=-200, y=100)
    lab.create_node(name="cloud-api-01", template=TEMPLATE_UBUNTU, x=-200, y=180)

    lab.create_node(name="ot-rtr", template=TEMPLATE_IOSV, x=200, y=50)
    lab.create_node(name="ot-sw", template=TEMPLATE_IOSVL2, x=200, y=150)
    lab.create_node(name="plc-sim-01", template=TEMPLATE_UBUNTU, x=350, y=150)
    lab.create_node(name="bms-01", template=TEMPLATE_WIN10, x=350, y=230)

    # US SITE
    lab.create_node(name="us-edge", template=TEMPLATE_IOSV, x=-300, y=-50)
    lab.create_node(name="us-sw", template=TEMPLATE_IOSVL2, x=-300, y=50)
    lab.create_node(name="us-ehr-01", template=TEMPLATE_WINSRV, x=-450, y=50)
    lab.create_node(name="us-iot-gw-01", template=TEMPLATE_UBUNTU, x=-450, y=130)
    lab.create_node(name="us-ad-01", template=TEMPLATE_WINSRV, x=-450, y=-30)

    # UK SITE
    lab.create_node(name="uk-edge", template=TEMPLATE_IOSV, x=0, y=-50)
    lab.create_node(name="uk-sw", template=TEMPLATE_IOSVL2, x=0, y=50)
    lab.create_node(name="uk-img-01", template=TEMPLATE_WINSRV, x=150, y=50)
    lab.create_node(name="uk-ehr-01", template=TEMPLATE_UBUNTU, x=150, y=-30)

    # SINGAPORE SITE
    lab.create_node(name="sg-edge", template=TEMPLATE_IOSV, x=-150, y=150)
    lab.create_node(name="sg-sw", template=TEMPLATE_IOSVL2, x=-150, y=250)
    lab.create_node(name="sg-web-01", template=TEMPLATE_UBUNTU, x=-300, y=250)
    lab.create_node(name="sg-db-01", template=TEMPLATE_UBUNTU, x=-300, y=330)

    # ----------------------------------------------------------------
    # LINKS
    # ----------------------------------------------------------------
    lab.create_link("internet", "eth0", "core-rtr", "Gi0/0")
    lab.create_link("core-rtr", "Gi0/1", "us-edge", "Gi0/0")
    lab.create_link("core-rtr", "Gi0/2", "uk-edge", "Gi0/0")
    lab.create_link("core-rtr", "Gi0/3", "sg-edge", "Gi0/0")
    lab.create_link("core-rtr", "Gi0/4", "cloud-rtr", "Gi0/0")
    lab.create_link("core-rtr", "Gi0/5", "soc-rtr", "Gi0/0")
    lab.create_link("core-rtr", "Gi0/6", "ot-rtr", "Gi0/0")

    lab.create_link("soc-rtr", "Gi0/1", "soc-sw", "Gi0/0")
    lab.create_link("soc-siem-01", "Ethernet0", "soc-sw", "Gi0/1")
    lab.create_link("soc-analyst-01", "Ethernet0", "soc-sw", "Gi0/2")

    lab.create_link("cloud-rtr", "Gi0/1", "cloud-sw", "Gi0/0")
    lab.create_link("cloud-web-01", "Ethernet0", "cloud-sw", "Gi0/1")
    lab.create_link("cloud-api-01", "Ethernet0", "cloud-sw", "Gi0/2")

    lab.create_link("ot-rtr", "Gi0/1", "ot-sw", "Gi0/0")
    lab.create_link("plc-sim-01", "Ethernet0", "ot-sw", "Gi0/1")
    lab.create_link("bms-01", "Ethernet0", "ot-sw", "Gi0/2")

    lab.create_link("us-edge", "Gi0/1", "us-sw", "Gi0/0")
    lab.create_link("us-ehr-01", "Ethernet0", "us-sw", "Gi0/1")
    lab.create_link("us-iot-gw-01", "Ethernet0", "us-sw", "Gi0/2")
    lab.create_link("us-ad-01", "Ethernet0", "us-sw", "Gi0/3")

    lab.create_link("uk-edge", "Gi0/1", "uk-sw", "Gi0/0")
    lab.create_link("uk-img-01", "Ethernet0", "uk-sw", "Gi0/1")
    lab.create_link("uk-ehr-01", "Ethernet0", "uk-sw", "Gi0/2")

    lab.create_link("sg-edge", "Gi0/1", "sg-sw", "Gi0/0")
    lab.create_link("sg-web-01", "Ethernet0", "sg-sw", "Gi0/1")
    lab.create_link("sg-db-01", "Ethernet0", "sg-sw", "Gi0/2")

    # ----------------------------------------------------------------
    # Autostart & start nodes
    # ----------------------------------------------------------------
    lab.get_nodes()
    for node in lab.nodes:
        try:
            node.get()
            node.auto_start = True
            node.update()
            node.start()
            print(f"[+] Node {node.name} set to autostart and started")
        except Exception as e:
            print(f"[!] Could not autostart {node.name}: {e}")

    apply_router_configs(lab)

    print("-----------------------------------------------------------------------")
    print("Nodes created, linked, autostart set, and router configs applied.")
    lab.links_summary()
    print("-----------------------------------------------------------------------")
    print(LAB_NAME + f" build is Complete on {SERVER_URL}. It is now safe to open the project in GNS3")
