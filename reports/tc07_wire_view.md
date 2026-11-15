# Wire View Report: `tc07_trace.csv`

## 1. Event Counters
| Event | Count |
| :--- | ---: |
| `RX_ACK` | 899 |
| `RX_DATA` | 1306 |
| `RX_NACK` | 144 |
| `RX_TRIM` | 144 |
| `SW_ECN` | 213 |
| `SW_TRIM` | 144 |
| `TX_DATA` | 1306 |
| `TX_NACK` | 144 |
| `TX_RTX` | 144 |

- **Unique Entropy Values (EVs) observed**: `16`
- **0-RTT SYN observed**: `True` | **EOM observed**: `True`

## 2. Key Packet Timeline (Wire View)
| Time (ns) | Event | Flow | PSN | CummACK | EV | DSCP | ECN | Flags | Size (B) | Extra |
| ---: | :--- | ---: | ---: | ---: | :--- | :--- | ---: | :--- | ---: | :--- |
| 0 | `TX_DATA` | 1 | 0 | 0 | `0x0001` | `0x20` | 0 | SYN | 4096 | - |
| 0 | `TX_DATA` | 2 | 0 | 0 | `0x0001` | `0x20` | 0 | SYN | 4096 | - |
| 0 | `TX_DATA` | 3 | 0 | 0 | `0x0001` | `0x20` | 0 | SYN | 4096 | - |
| 0 | `TX_DATA` | 4 | 0 | 0 | `0x0001` | `0x20` | 0 | SYN | 4096 | - |
| 0 | `TX_DATA` | 5 | 0 | 0 | `0x0001` | `0x20` | 0 | SYN | 4096 | - |
| 0 | `TX_DATA` | 6 | 0 | 0 | `0x0001` | `0x20` | 0 | SYN | 4096 | - |
| 7966 | `RX_DATA` | 1 | 0 | 0 | `0x0001` | `0x20` | 0 | SYN | 4096 | - |
| 8293 | `RX_DATA` | 3 | 0 | 0 | `0x0001` | `0x20` | 0 | SYN | 4096 | - |
| 9276 | `RX_DATA` | 4 | 0 | 0 | `0x0001` | `0x20` | 0 | SYN | 4096 | - |
| 9604 | `RX_DATA` | 5 | 0 | 0 | `0x0001` | `0x20` | 0 | SYN | 4096 | - |
| 10881 | `SW_ECN` | 4 | 7 | 0 | `0x0008` | `0x20` | 3 | - | 4096 | ECNQueue |
| 10915 | `RX_DATA` | 2 | 0 | 0 | `0x0001` | `0x20` | 0 | SYN | 4096 | - |
| 11192 | `SW_ECN` | 5 | 10 | 0 | `0x000b` | `0x20` | 3 | - | 4096 | ECNQueue |
| 11208 | `SW_ECN` | 3 | 4 | 0 | `0x0005` | `0x20` | 3 | - | 4096 | ECNQueue |
| 11208 | `SW_ECN` | 6 | 4 | 0 | `0x0005` | `0x20` | 3 | - | 4096 | ECNQueue |
| 11519 | `SW_ECN` | 2 | 8 | 0 | `0x0009` | `0x20` | 3 | - | 4096 | ECNQueue |
| 12225 | `RX_DATA` | 6 | 0 | 0 | `0x0001` | `0x20` | 0 | SYN | 4096 | - |
| 13996 | `RX_ACK` | 1 | 0 | 1 | `0x0001` | `0x30` | 0 | - | 64 | - |
| 14324 | `RX_ACK` | 3 | 0 | 1 | `0x0001` | `0x30` | 0 | - | 64 | - |
| 14979 | `RX_ACK` | 2 | 1 | 0 | `0x0002` | `0x30` | 0 | - | 64 | - |
| 15307 | `RX_ACK` | 4 | 0 | 1 | `0x0001` | `0x30` | 0 | - | 64 | - |
| 15635 | `RX_ACK` | 5 | 0 | 1 | `0x0001` | `0x30` | 0 | - | 64 | - |
| 16796 | `SW_TRIM` | 6 | 7 | 0 | `0x0008` | `0x30` | 3 | TRIM | 64 | ARRIVING_TRIM |
| 17124 | `SW_TRIM` | 2 | 15 | 0 | `0x0000` | `0x30` | 3 | TRIM | 64 | ARRIVING_TRIM |
| 17451 | `SW_TRIM` | 6 | 14 | 0 | `0x000f` | `0x30` | 3 | TRIM | 64 | BOOTED_TRIM |
| 17451 | `SW_TRIM` | 4 | 8 | 0 | `0x0009` | `0x30` | 3 | TRIM | 64 | BOOTED_TRIM |
| 17779 | `SW_TRIM` | 5 | 15 | 0 | `0x0000` | `0x30` | 3 | TRIM | 64 | BOOTED_TRIM |
| 18107 | `SW_TRIM` | 6 | 8 | 0 | `0x0009` | `0x30` | 3 | TRIM | 64 | ARRIVING_TRIM |
| 18129 | `RX_TRIM` | 6 | 7 | 4 | `0x0008` | `0x30` | 3 | TRIM | 64 | - |
| 18129 | `TX_NACK` | 6 | 7 | 4 | `0x0008` | `0x30` | 3 | TRIM | 64 | - |
| 18134 | `RX_TRIM` | 2 | 15 | 5 | `0x0000` | `0x30` | 3 | TRIM | 64 | - |
| 18134 | `TX_NACK` | 2 | 15 | 5 | `0x0000` | `0x30` | 3 | TRIM | 64 | - |
| 18434 | `SW_TRIM` | 1 | 8 | 0 | `0x0009` | `0x30` | 3 | TRIM | 64 | ARRIVING_TRIM |
| 18467 | `RX_TRIM` | 6 | 14 | 4 | `0x000f` | `0x30` | 3 | TRIM | 64 | - |
| 18467 | `TX_NACK` | 6 | 14 | 4 | `0x000f` | `0x30` | 3 | TRIM | 64 | - |
| 18472 | `RX_TRIM` | 4 | 8 | 4 | `0x0009` | `0x30` | 3 | TRIM | 64 | - |
| 18472 | `TX_NACK` | 4 | 8 | 4 | `0x0009` | `0x30` | 3 | TRIM | 64 | - |
| 18762 | `SW_TRIM` | 3 | 11 | 0 | `0x000c` | `0x30` | 3 | TRIM | 64 | BOOTED_TRIM |
| 18805 | `RX_TRIM` | 5 | 15 | 5 | `0x0000` | `0x30` | 3 | TRIM | 64 | - |
| 18805 | `TX_NACK` | 5 | 15 | 5 | `0x0000` | `0x30` | 3 | TRIM | 64 | - |
