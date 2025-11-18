import logging
from gns3fy import Gns3Connector, Project

LAB_NAME = "cit480-operation-nightingale-1"
BASE_IP = "http://10.48.229."

# Read last octets from datastore file
try:
    with open("datastore", "r") as f:
        content = f.read().strip()
        SERVER_LAST_OCTETS = [int(octet.strip()) for octet in content.split(",") if octet.strip().isdigit()]
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
TEMPLATE_UBUNTU = "ubuntu"
TEMPLATE_CLOUD = "Cloud"

# IOS router configs with IPs + OSPF + DHCP
ROUTER_CONFIGS = {
    "core-rtr": """hostname core-rtr
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

    "us-edge": """hostname us-edge
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

    "uk-edge": """hostname uk-edge
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

    "sg-edge": """hostname sg-edge
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

    "cloud-rtr": """hostname cloud-rtr
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

    "soc-rtr": """hostname soc-rtr
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

    "ot-rtr": """hostname ot-rtr
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

def apply_router_configs(lab: Project):
    for router_name, cfg in ROUTER_CONFIGS.items():
        try:
            node = lab.get_node(router_name)
            node.get()
            node.update(config=cfg)
            print(f"[+] Applied config to {router_name}")
        except Exception as e:
            print(f"[!] Failed to apply config to {router_name}: {e}")

for SERVER_URL in SERVER_URLS:
    server = Gns3Connector(url=SERVER_URL, user=GNS3_USER, cred=GNS3_PW)
    print("Connecting to GNS3 server", server.get_version(), "at", SERVER_URL)

    server.create_project(name=LAB_NAME)
    print(f"Project '{LAB_NAME}' created on {SERVER_URL}")

    lab = Project(name=LAB_NAME, connector=server)
    lab.get()
    lab.open()

    available_templates = [template["name"] for template in server.get_templates()]
    logging.debug(f"Available Templates: {available_templates}")

    # CORE / INTERNET / SOC / CLOUD / OT
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

    # LINKS
    lab.create_link("internet", "eth0", "core-rtr", "Gi0/0")
    lab.create_link("core-rtr", "Gi0/1", "us-edge", "Gi0/0")
    lab.create_link("core-rtr", "Gi0/2", "uk-edge", "Gi0/0")
    lab.create_link("core-rtr", "Gi0/3", "sg-edge", "Gi0/0")
    lab.create_link("core-rtr", "Gi0/4", "cloud-rtr", "Gi0/0")
    lab.create_link("core-rtr", "Gi0/5", "soc-rtr", "Gi0/0")
    lab.create_link("core-rtr", "Gi0/6", "ot-rtr", "Gi0/0")

    lab.create_link("soc-rtr", "Gi0/1", "soc-sw", "Gi0/0")
    lab.create_link("soc-siem-01", "NIC1", "soc-sw", "Gi0/1")
    lab.create_link("soc-analyst-01", "NIC1", "soc-sw", "Gi0/2")

    lab.create_link("cloud-rtr", "Gi0/1", "cloud-sw", "Gi0/0")
    lab.create_link("cloud-web-01", "NIC1", "cloud-sw", "Gi0/1")
    lab.create_link("cloud-api-01", "NIC1", "cloud-sw", "Gi0/2")

    lab.create_link("ot-rtr", "Gi0/1", "ot-sw", "Gi0/0")
    lab.create_link("plc-sim-01", "NIC1", "ot-sw", "Gi0/1")
    lab.create_link("bms-01", "NIC1", "ot-sw", "Gi0/2")

    lab.create_link("us-edge", "Gi0/1", "us-sw", "Gi0/0")
    lab.create_link("us-ehr-01", "Ethernet0", "us-sw", "Gi0/1")
    lab.create_link("us-iot-gw-01", "NIC1", "us-sw", "Gi0/2")
    lab.create_link("us-ad-01", "Ethernet0", "us-sw", "Gi0/3")

    lab.create_link("uk-edge", "Gi0/1", "uk-sw", "Gi0/0")
    lab.create_link("uk-img-01", "Ethernet0", "uk-sw", "Gi0/1")
    lab.create_link("uk-ehr-01", "NIC1", "uk-sw", "Gi0/2")

    lab.create_link("sg-edge", "Gi0/1", "sg-sw", "Gi0/0")
    lab.create_link("sg-web-01", "NIC1", "sg-sw", "Gi0/1")
    lab.create_link("sg-db-01", "NIC1", "sg-sw", "Gi0/2")

    # Autostart & start nodes
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
