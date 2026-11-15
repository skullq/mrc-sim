# Wire View Report: `tc01_trace.csv`

## 1. Event Counters
| Event | Count |
| :--- | ---: |
| `RX_ACK` | 21 |
| `RX_DATA` | 66 |
| `TX_DATA` | 66 |

- **Unique Entropy Values (EVs) observed**: `16`
- **0-RTT SYN observed**: `True` | **EOM observed**: `True`

## 2. Key Packet Timeline (Wire View)
| Time (ns) | Event | Flow | PSN | CummACK | EV | DSCP | ECN | Flags | Size (B) | Extra |
| ---: | :--- | ---: | ---: | ---: | :--- | :--- | ---: | :--- | ---: | :--- |
| 0 | `TX_DATA` | 1 | 0 | 0 | `0x0001` | `0x20` | 0 | SYN | 4096 | - |
| 7966 | `RX_DATA` | 1 | 0 | 0 | `0x0001` | `0x20` | 0 | SYN | 4096 | - |
| 13996 | `RX_ACK` | 1 | 0 | 1 | `0x0001` | `0x30` | 0 | - | 64 | - |
| 15307 | `RX_ACK` | 1 | 4 | 5 | `0x0005` | `0x30` | 0 | - | 64 | - |
| 16618 | `RX_ACK` | 1 | 8 | 9 | `0x0009` | `0x30` | 0 | - | 64 | - |
| 17928 | `RX_ACK` | 1 | 12 | 13 | `0x000d` | `0x30` | 0 | - | 64 | - |
| 19239 | `RX_ACK` | 1 | 16 | 17 | `0x0004` | `0x30` | 0 | - | 64 | - |
| 37168 | `TX_DATA` | 1 | 65 | 0 | `0x0005` | `0x20` | 0 | EOM | 128 | - |
