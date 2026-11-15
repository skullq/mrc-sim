# Wire View Report: `tc09d_bts_trace.csv`

## 1. Event Counters
| Event | Count |
| :--- | ---: |
| `RX_ACK` | 1634 |
| `RX_BTS` | 555 |
| `RX_DATA` | 1916 |
| `RX_NACK` | 590 |
| `RX_TRIM` | 590 |
| `SW_BTS` | 555 |
| `SW_ECN` | 1671 |
| `SW_SKIP_SHORT_TRIM` | 6 |
| `SW_TRIM` | 1165 |
| `TX_DATA` | 1834 |
| `TX_NACK` | 590 |
| `TX_RTX` | 1317 |

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
| 0 | `TX_DATA` | 7 | 0 | 0 | `0x0001` | `0x20` | 0 | SYN | 4096 | - |
| 0 | `TX_DATA` | 8 | 0 | 0 | `0x0001` | `0x20` | 0 | SYN | 4096 | - |
| 0 | `TX_DATA` | 9 | 0 | 0 | `0x0001` | `0x20` | 0 | SYN | 4096 | - |
| 0 | `TX_DATA` | 10 | 0 | 0 | `0x0001` | `0x20` | 0 | SYN | 4096 | - |
| 0 | `TX_DATA` | 11 | 0 | 0 | `0x0001` | `0x20` | 0 | SYN | 4096 | - |
| 0 | `TX_DATA` | 12 | 0 | 0 | `0x0001` | `0x20` | 0 | SYN | 4096 | - |
| 0 | `TX_DATA` | 13 | 0 | 0 | `0x0001` | `0x20` | 0 | SYN | 4096 | - |
| 0 | `TX_DATA` | 14 | 0 | 0 | `0x0001` | `0x20` | 0 | SYN | 4096 | - |
| 5310 | `RX_DATA` | 13 | 0 | 0 | `0x0001` | `0x20` | 0 | SYN | 4096 | - |
| 5966 | `RX_DATA` | 14 | 0 | 0 | `0x0001` | `0x20` | 0 | SYN | 4096 | - |
| 6276 | `SW_TRIM` | 13 | 7 | 0 | `0x0008` | `0x30` | 0 | TRIM | 64 | BOOTED_TRIM |
| 6604 | `SW_ECN` | 6 | 0 | 0 | `0x0001` | `0x20` | 3 | - | 4096 | ECNQueue |
| 6604 | `SW_TRIM` | 14 | 5 | 0 | `0x0006` | `0x30` | 0 | TRIM | 64 | ARRIVING_TRIM |
| 6604 | `SW_BTS` | 14 | 5 | 0 | `0x0006` | `0x30` | 0 | TRIM,BTS | 64 | F6_BTS_ON_TRIM |
| 6932 | `SW_ECN` | 9 | 1 | 0 | `0x0002` | `0x20` | 3 | - | 4096 | ECNQueue |
| 6932 | `SW_ECN` | 7 | 2 | 0 | `0x0003` | `0x20` | 3 | - | 4096 | ECNQueue |
| 6932 | `SW_TRIM` | 1 | 0 | 0 | `0x0001` | `0x30` | 0 | TRIM | 64 | ARRIVING_TRIM |
| 6932 | `SW_BTS` | 1 | 0 | 0 | `0x0001` | `0x30` | 0 | TRIM,BTS | 64 | F6_BTS_ON_TRIM |
| 6932 | `SW_TRIM` | 3 | 0 | 0 | `0x0001` | `0x30` | 0 | TRIM | 64 | ARRIVING_TRIM |
| 6932 | `SW_BTS` | 3 | 0 | 0 | `0x0001` | `0x30` | 0 | TRIM,BTS | 64 | F6_BTS_ON_TRIM |
| 7259 | `SW_ECN` | 8 | 2 | 0 | `0x0003` | `0x20` | 3 | - | 4096 | ECNQueue |
| 7259 | `SW_ECN` | 9 | 3 | 0 | `0x0004` | `0x20` | 3 | - | 4096 | ECNQueue |
| 7259 | `SW_TRIM` | 13 | 6 | 0 | `0x0007` | `0x30` | 0 | TRIM | 64 | ARRIVING_TRIM |
| 7259 | `SW_BTS` | 13 | 6 | 0 | `0x0007` | `0x30` | 0 | TRIM,BTS | 64 | F6_BTS_ON_TRIM |
| 7587 | `SW_TRIM` | 2 | 1 | 0 | `0x0002` | `0x30` | 0 | TRIM | 64 | ARRIVING_TRIM |
| 7587 | `SW_BTS` | 2 | 1 | 0 | `0x0002` | `0x30` | 0 | TRIM,BTS | 64 | F6_BTS_ON_TRIM |
| 7609 | `RX_TRIM` | 13 | 7 | 4 | `0x0008` | `0x30` | 0 | TRIM | 64 | - |
| 7609 | `TX_NACK` | 13 | 7 | 4 | `0x0008` | `0x30` | 0 | TRIM | 64 | - |
| 7864 | `TX_RTX` | 14 | 5 | 0 | `0x000e` | `0x20` | 0 | RTX | 4096 | - |
| 7915 | `SW_TRIM` | 7 | 0 | 0 | `0x0001` | `0x30` | 0 | TRIM | 64 | BOOTED_TRIM |
| 8192 | `TX_RTX` | 1 | 0 | 0 | `0x000e` | `0x20` | 0 | RTX | 4096 | - |
| 8192 | `TX_RTX` | 3 | 0 | 0 | `0x000f` | `0x20` | 0 | RTX | 4096 | - |
| 8242 | `SW_TRIM` | 14 | 6 | 0 | `0x0007` | `0x30` | 0 | TRIM | 64 | ARRIVING_TRIM |
| 8242 | `SW_BTS` | 14 | 6 | 0 | `0x0007` | `0x30` | 0 | TRIM,BTS | 64 | F6_BTS_ON_TRIM |
