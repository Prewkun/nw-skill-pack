---
name: delta-coding
description: Generate Python or PLC code to communicate with a Delta SD3 Smart Screwdriving System via Modbus TCP/RTU or TCP/IP. Use when the user calls /delta-coding, mentions Delta SD3 screwdriving, asks to control a smart screwdriver controller, or describes tasks like reading tightening results, switching parameters, clearing errors, reading DI/DO status, or any Modbus/TCP handshake with an SD3 controller. Also trigger proactively any time the user describes what the SD3 should DO and expects communication code out.
argument-hint: "<describe the communication task>"
---

# /delta-coding

Generate production-quality Modbus TCP / TCP/IP communication code for the **Delta SD3 Smart Screwdriving System**. Always search the local KB before writing code — never guess register addresses or function codes.

## Usage

```
/delta-coding <describe the task>
```

Describe what you need to do with the SD3 controller: @$1

If no task is provided, ask the user what they want to do with the controller.

---

## Step 1 — Clarify protocol and language

Before searching, confirm these two things (ask if not clear):

1. **Protocol**: `Modbus TCP`, `Modbus RTU`, or `TCP/IP`?
   - Modbus TCP/RTU → uses hex register addresses (C8–D1) for handshake
   - TCP/IP → uses byte-offset tables; supports subscription (#10/#11) for real-time status push
2. **Language**: Python, C#, PLC (Structured Text), or other?

---

## Step 2 — Search the KB

Run the search script to find the relevant function codes.
**Replace `<REPO_PATH>` with your clone path.**

```bash
cd "<REPO_PATH>/user/delta-coding"
python scripts/delta_search.py "<keywords from the user's task>" -n 8
```

**Protocol filter** (use to narrow results):
```bash
python scripts/delta_search.py "switch parameter" --protocol Modbus
python scripts/delta_search.py "read result status" --protocol TCPIP
```

**Exact function code lookup** (when code number is known):
```bash
python scripts/delta_search.py 302 --code --verbose
python scripts/delta_search.py 750 --code --verbose
```

**Category filter** (for broad tasks):
```bash
python scripts/delta_search.py "tightening" --category Results
python scripts/delta_search.py "login permission" --category Controller
```

Extract 2–4 keyword phrases from the user's task. Run multiple searches if the task covers multiple areas. Read all output carefully.

**Examples of good keyword choices:**
- Switch tightening parameter → search `"switch parameter manual"`
- Read OK/NOK result → search `"read tightening result status"` and `"production report"`
- Clear alarms → search `"clear errors alarms"`
- Read DI/DO status → search `"DI DO status read"`
- Subscription real-time data → search `"subscription operational status"` (TCP/IP only)
- Change ethernet/IP settings → search `"ethernet IP settings"`
- Login / permissions → search `"login permissions password"`

---

## Step 3 — Write the communication code

Using **only** function codes found in KB output, write complete, runnable code.

### Hard rules (never break these)

1. **Handshake order** — always write request registers first, THEN set `CE = 1` (Modbus) or byte 13–14 = 1 (TCP/IP) last to trigger execution.
2. **Poll return status** — check `D0` (Modbus) or bytes 17–18 (TCP/IP) for `1 = OK` before reading data.
3. **Never guess register addresses** — use only addresses from KB search output.
4. **Modbus word order** — values wider than 16 bits split into `(L)` low word and `(H)` high word registers.
5. **TCP/IP byte order** — all 16-bit values are **Little-Endian** (LSB first).
6. **Default ports** — Modbus TCP: 502 | TCP/IP: 1001 | default IP: 192.168.1.11
7. **Connection hygiene** — open socket → execute handshake → close or keep-alive as needed.
8. **Error handling** — always check return status; map error codes using KB output.

### Modbus TCP handshake template (Python)

```python
from pymodbus.client import ModbusTcpClient

CONTROLLER_IP = "192.168.1.11"
MODBUS_PORT   = 502

# Register base (handshake window: 0xC8–0xD1 = 200–209 decimal)
REG_BASE = 0xC8  # 200

def write_registers(client, values: dict[int, int]):
    """Write {offset: value} dict into the handshake window."""
    # Write all registers except CE (trigger) first
    for offset, val in sorted(values.items()):
        if offset != 0xCE - REG_BASE:
            client.write_register(REG_BASE + offset, val)
    # Write CE = 1 last to trigger execution
    client.write_register(0xCE, 1)

def wait_return_status(client, expected_fc: int, timeout: float = 3.0):
    import time
    t0 = time.time()
    while time.time() - t0 < timeout:
        result = client.read_holding_registers(0xCF, 3)
        if result.isError():
            raise RuntimeError("Modbus read error")
        fc, status, err_code = result.registers
        if fc == expected_fc:
            return status, err_code
        time.sleep(0.05)
    raise TimeoutError(f"No response for FC#{expected_fc} within {timeout}s")

# Example: FC#302 — switch parameter to ID=5, screw qty=10
with ModbusTcpClient(CONTROLLER_IP, port=MODBUS_PORT) as client:
    write_registers(client, {
        0x00: 302,    # C8 = function code
        0x01: 0,      # C9 = version
        0x02: 0,      # CA = Tool 1
        0x03: 5,      # CB = parameter ID
        0x04: 10,     # CC = screw qty (L)
        0x05: 0,      # CD = screw qty (H)
    })
    status, err = wait_return_status(client, expected_fc=302)
    if status == 1:
        print("Parameter switched OK")
    else:
        print(f"NOK — error code {err}")
```

### TCP/IP handshake template (Python)

```python
import socket, struct

CONTROLLER_IP = "192.168.1.11"
TCPIP_PORT    = 1001

def tcpip_request(fc: int, payload: bytes) -> bytes:
    """Send a TCP/IP handshake request and return the full response."""
    # Build request: fc (2B LE) + version (2B) + payload + request_trigger (2B = 0x0001)
    header  = struct.pack("<HH", fc, 0)          # function code + version
    trigger = struct.pack("<H", 1)               # request to send command
    frame   = header + payload + trigger
    with socket.create_connection((CONTROLLER_IP, TCPIP_PORT), timeout=5) as s:
        s.sendall(frame)
        resp = b""
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            resp += chunk
            if len(resp) >= 20:
                break
    return resp

# Example: FC#302 — switch parameter (TCP/IP)
payload = struct.pack("<HHHH", 0, 5, 10, 0)  # Tool1, paramID=5, qty_L=10, qty_H=0
resp = tcpip_request(302, payload)

ret_fc     = struct.unpack_from("<H", resp, 14)[0]
ret_status = struct.unpack_from("<H", resp, 16)[0]
ret_err    = struct.unpack_from("<H", resp, 18)[0]

if ret_status == 1:
    print("Parameter switched OK")
else:
    print(f"NOK — FC={ret_fc}, error={ret_err}")
```

---

## Step 4 — Confirm output to the user

After writing the code, confirm:
- Which function codes were used and what they do
- Protocol assumed (Modbus TCP / TCP/IP)
- Controller IP and port used (defaults shown; user may need to change)
- Any assumptions about parameter IDs, tool selection, or screw quantities
- What the user needs to verify on the controller side (IP address, permissions login if needed)

---

## Common task → function code map

| Task | Modbus FC | TCP/IP FC |
|---|---|---|
| Switch parameter (manual mode) | #302 | #302 |
| Switch sequence (manual mode) | #303 | #303 |
| Read operational status | poll 0x1E00–0x1FFF registers | #50 (or subscribe #10) |
| Clear all AL/NG/WN errors | #402 | #402 |
| Reset operation progress | #403 | #403 |
| Read tightening result (production report) | #750 | #750 |
| Read error report | #752 | #752 |
| Read parameter | #150 | #150 |
| Login (for write operations) | #500 | #500 |
| Read ethernet settings | #550 | #550 |
| Read DI/DO functions | #553 | #553 |
| Subscribe real-time status | N/A | #10 |
