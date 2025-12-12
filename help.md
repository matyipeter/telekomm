# 🛜 Network Exam Survival Guide (Linux)

A comprehensive cheat sheet for configuring interfaces, routing, NAT, firewalls, and services using `ip` and `iptables`.

---

## 1. 🏗️ Foundations: Interfaces & IPs
*First, ensure the lights are on and the devices have names.*

### Check Status
```bash
ip link                 # Are interfaces UP or DOWN?
ip addr                 # Do they have IP addresses?
```

### Turn On Interface
```bash
ip link set dev eth0 up
```

### Assign IP Address
```bash
# Syntax: ip addr add [IP]/[MASK] dev [INTERFACE]
ip addr add 192.168.1.1/24 dev eth0

# ⚠️ Mistake? Delete it:
ip addr del 192.168.1.1/24 dev eth0
```

---

## 2. 🚚 Routing: Moving Packets
*If the router doesn't know the way, the packet dies.*

### Default Gateway (For PCs/End Devices)
*Tell the device: "If you don't know where to send it, send it to the router."*
```bash
# Syntax: ip route add default via [ROUTER_IP]
ip route add default via 192.168.1.254
```

### Static Route (For Routers)
*Tell the router: "To reach Network X, go through Neighbor Y."*
```bash
# Syntax: ip route add [DEST_NET]/[MASK] via [NEXT_HOP_IP]
ip route add 10.0.0.0/24 via 192.168.1.2

# 🧠 Pro Tip: Route Aggregation
# If you have 1.8.8.0/24 and 1.8.9.0/24 behind a router, 
# you can route the whole block at once:
ip route add 1.8.0.0/16 via 192.168.1.2
```

---

## 3. 🎭 NAT (Network Address Translation)
*Hiding internal IPs or exposing internal servers.*

### SNAT (Masquerading) - Accessing the Internet
*Allows private IPs (e.g., 192.168.x) to talk to the internet using the router's public IP.*
```bash
# -t nat: NAT table
# -A POSTROUTING: Change source AFTER routing
# -o: Output interface (WAN/Internet side)
# -s: (Optional) Source subnet to allow
iptables -t nat -A POSTROUTING -o eth0 -s 192.168.1.0/24 -j MASQUERADE
```

### DNAT (Port Forwarding) - Exposing a Server
*Forward traffic hitting the Router's Public IP to an Internal Private IP.*
```bash
# -A PREROUTING: Change destination BEFORE routing
# -i: Input interface (WAN/Internet side)
# --dport: The port they are knocking on (e.g., 80 for Web)
iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 80 -j DNAT --to-destination 10.0.0.20:80
```

### SSH Redirection (Specific DNAT)
*Trick users: They SSH to the Router/DNS, but land on a different PC.*
```bash
# Redirect SSH (port 22) destined for 10.0.0.5 -> to 192.168.1.3
iptables -t nat -A PREROUTING -d 10.0.0.5 -p tcp --dport 22 -j DNAT --to-destination 192.168.1.3:22
```

---

## 4. 🛡️ Firewall: Blocking Traffic
*The bouncer at the door.*

### Block Traffic Passing Through
*Use the `FORWARD` chain. Use `-I` (Insert) to put it at the top!*
```bash
# Block PC (10.0.0.30) from going out to the internet (eth0)
iptables -I FORWARD -s 10.0.0.30 -o eth0 -j DROP

# Block traffic attempting to reach that PC from outside
iptables -I FORWARD -d 10.0.0.30 -i eth0 -j DROP
```

### Verify Rules
```bash
iptables -L -v -n        # Check Filter rules (DROP/ACCEPT)
iptables -t nat -L -v -n # Check NAT rules
```

---

## 5. 🔎 Troubleshooting & Monitoring
*Why is it broken?*

### Connectivity
```bash
ping 8.8.8.8             # Can I reach the internet?
ping 192.168.1.1         # Can I reach the gateway?
```

### Layer 2 (MAC Addresses)
```bash
arp -n                   # Who are my neighbors? (Empty = Layer 2 issue)
```

### Packet Sniffing (The "X-Ray")
*Run this in a separate terminal to see what's happening on the wire.*
```bash
tcpdump -lvvn
# or specifically for ICMP (ping):
tcpdump -i eth0 -n icmp
```

### STP (Spanning Tree) - For Switches
*Fixing loops in the network.*
```bash
brctl show               # Check if STP is on
ip link set br0 type bridge stp_state 1  # Turn STP ON
brctl showstp br0        # Check port state (blocking/forwarding)
```

---

## 6. 🌍 Services (DNS & SSH)

### DNS Configuration
*Mapping names (elek.hu) to IPs.*

**Client Side (Where to ask):**
```bash
# Warning: > overwrites, >> appends.
echo "nameserver 10.0.0.5" > /etc/resolv.conf
```

**Server Side (The "Phonebook"):**
```bash
# Simple way: Edit hosts file
echo "192.168.1.10 elek.hu" >> /etc/hosts
```

### SSH Setup
**Server:**
```bash
systemctl start ssh      # Start service
/usr/sbin/sshd           # Start daemon manually (if needed)
```
**Client:**
```bash
ssh-keygen               # Generate keys
cat ~/.ssh/id_rsa.pub    # Copy this output!
ssh root@192.168.1.10    # Connect
```
**Authorize (On Server):**
Paste the client's key into: `~/.ssh/authorized_keys`
