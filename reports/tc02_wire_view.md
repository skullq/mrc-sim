# Wire View Report: `tc02_trace.csv`

## 1. Event Counters
| Event | Count |
| :--- | ---: |
| `RX_ACK` | 730 |
| `RX_DATA` | 1050 |
| `RX_NACK` | 306 |
| `RX_TRIM` | 306 |
| `SW_ECN` | 552 |
| `SW_TRIM` | 306 |
| `TX_DATA` | 1048 |
| `TX_NACK` | 306 |
| `TX_RTX` | 308 |

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
| 7966 | `RX_DATA` | 1 | 0 | 0 | `0x0001` | `0x20` | 0 | SYN | 4096 | - |
| 8293 | `RX_DATA` | 3 | 0 | 0 | `0x0001` | `0x20` | 0 | SYN | 4096 | - |
| 9225 | `SW_ECN` | 3 | 5 | 0 | `0x0006` | `0x20` | 3 | - | 4096 | ECNQueue |
| 9276 | `RX_DATA` | 7 | 0 | 0 | `0x0001` | `0x20` | 0 | SYN | 4096 | - |
| 9553 | `SW_ECN` | 5 | 5 | 0 | `0x0006` | `0x20` | 3 | - | 4096 | ECNQueue |
| 9604 | `RX_DATA` | 5 | 0 | 0 | `0x0001` | `0x20` | 0 | SYN | 4096 | - |
| 9881 | `SW_ECN` | 2 | 5 | 0 | `0x0006` | `0x20` | 3 | - | 4096 | ECNQueue |
| 9932 | `RX_DATA` | 8 | 0 | 0 | `0x0001` | `0x20` | 0 | SYN | 4096 | - |
| 10208 | `SW_ECN` | 6 | 6 | 0 | `0x0007` | `0x20` | 3 | - | 4096 | ECNQueue |
| 10536 | `SW_ECN` | 1 | 6 | 0 | `0x0007` | `0x20` | 3 | - | 4096 | ECNQueue |
| 10587 | `RX_DATA` | 4 | 0 | 0 | `0x0001` | `0x20` | 0 | SYN | 4096 | - |
| 10915 | `RX_DATA` | 2 | 0 | 0 | `0x0001` | `0x20` | 0 | SYN | 4096 | - |
| 11553 | `SW_TRIM` | 6 | 3 | 0 | `0x0004` | `0x30` | 3 | TRIM | 64 | BOOTED_TRIM |
| 11881 | `SW_TRIM` | 7 | 6 | 0 | `0x0007` | `0x30` | 3 | TRIM | 64 | BOOTED_TRIM |
| 12208 | `SW_TRIM` | 5 | 2 | 0 | `0x0003` | `0x30` | 3 | TRIM | 64 | BOOTED_TRIM |
| 12208 | `SW_TRIM` | 3 | 7 | 0 | `0x0008` | `0x30` | 3 | TRIM | 64 | ARRIVING_TRIM |
| 12536 | `SW_TRIM` | 5 | 7 | 0 | `0x0008` | `0x30` | 3 | TRIM | 64 | BOOTED_TRIM |
| 12864 | `SW_TRIM` | 7 | 3 | 0 | `0x0004` | `0x30` | 3 | TRIM | 64 | BOOTED_TRIM |
| 12886 | `RX_TRIM` | 6 | 3 | 0 | `0x0004` | `0x30` | 3 | TRIM | 64 | - |
| 12886 | `TX_NACK` | 6 | 3 | 0 | `0x0004` | `0x30` | 3 | TRIM | 64 | - |
| 12891 | `RX_TRIM` | 7 | 6 | 2 | `0x0007` | `0x30` | 3 | TRIM | 64 | - |
| 12891 | `TX_NACK` | 7 | 6 | 2 | `0x0007` | `0x30` | 3 | TRIM | 64 | - |
| 13192 | `SW_TRIM` | 7 | 8 | 0 | `0x0009` | `0x30` | 3 | TRIM | 64 | BOOTED_TRIM |
| 13224 | `RX_TRIM` | 5 | 2 | 2 | `0x0003` | `0x30` | 3 | TRIM | 64 | - |
| 13224 | `TX_NACK` | 5 | 2 | 2 | `0x0003` | `0x30` | 3 | TRIM | 64 | - |
| 13229 | `RX_TRIM` | 3 | 7 | 2 | `0x0008` | `0x30` | 3 | TRIM | 64 | - |
| 13229 | `TX_NACK` | 3 | 7 | 2 | `0x0008` | `0x30` | 3 | TRIM | 64 | - |
| 13519 | `SW_TRIM` | 3 | 2 | 0 | `0x0003` | `0x30` | 3 | TRIM | 64 | BOOTED_TRIM |
| 13562 | `RX_TRIM` | 5 | 7 | 2 | `0x0008` | `0x30` | 3 | TRIM | 64 | - |
| 13562 | `TX_NACK` | 5 | 7 | 2 | `0x0008` | `0x30` | 3 | TRIM | 64 | - |
| 13847 | `SW_TRIM` | 7 | 9 | 0 | `0x000a` | `0x30` | 3 | TRIM | 64 | BOOTED_TRIM |
| 13895 | `RX_TRIM` | 7 | 3 | 2 | `0x0004` | `0x30` | 3 | TRIM | 64 | - |
