# Wire View Report: `tc09b_trace.csv`

## 1. Event Counters
| Event | Count |
| :--- | ---: |
| `RX_ACK` | 747 |
| `RX_DATA` | 1057 |
| `RX_NACK` | 294 |
| `RX_TRIM` | 294 |
| `SW_ECN` | 562 |
| `SW_TRIM` | 295 |
| `TX_DATA` | 1049 |
| `TX_NACK` | 294 |
| `TX_RTX` | 303 |

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
| 0 | `TX_DATA` | 9 | 0 | 0 | `0x0001` | `0x20` | 0 | SYN,EOM | 128 | - |
| 6061 | `RX_DATA` | 9 | 0 | 0 | `0x0001` | `0x20` | 0 | SYN | 128 | - |
| 7966 | `RX_DATA` | 1 | 0 | 0 | `0x0001` | `0x20` | 0 | SYN | 4096 | - |
| 8293 | `RX_DATA` | 2 | 0 | 0 | `0x0001` | `0x20` | 0 | SYN | 4096 | - |
| 8621 | `RX_DATA` | 5 | 0 | 0 | `0x0001` | `0x20` | 0 | SYN | 4096 | - |
| 9276 | `RX_DATA` | 8 | 0 | 0 | `0x0001` | `0x20` | 0 | SYN | 4096 | - |
| 9553 | `SW_ECN` | 7 | 7 | 0 | `0x0008` | `0x20` | 3 | - | 4096 | ECNQueue |
| 9553 | `SW_ECN` | 3 | 7 | 0 | `0x0008` | `0x20` | 3 | - | 4096 | ECNQueue |
| 9604 | `RX_DATA` | 4 | 0 | 0 | `0x0001` | `0x20` | 0 | SYN | 4096 | - |
| 9881 | `SW_ECN` | 4 | 6 | 0 | `0x0007` | `0x20` | 3 | - | 4096 | ECNQueue |
| 9881 | `SW_ECN` | 7 | 8 | 0 | `0x0009` | `0x20` | 3 | - | 4096 | ECNQueue |
| 9932 | `RX_DATA` | 7 | 0 | 0 | `0x0001` | `0x20` | 0 | SYN | 4096 | - |
| 10208 | `SW_ECN` | 5 | 9 | 0 | `0x000a` | `0x20` | 3 | - | 4096 | ECNQueue |
| 10587 | `RX_DATA` | 3 | 0 | 0 | `0x0001` | `0x20` | 0 | SYN | 4096 | - |
| 11553 | `SW_TRIM` | 6 | 2 | 0 | `0x0003` | `0x30` | 3 | TRIM | 64 | BOOTED_TRIM |
| 11881 | `SW_TRIM` | 4 | 5 | 0 | `0x0006` | `0x30` | 3 | TRIM | 64 | ARRIVING_TRIM |
| 12092 | `RX_ACK` | 9 | 0 | 1 | `0x0001` | `0x30` | 0 | - | 64 | - |
| 12208 | `SW_TRIM` | 1 | 3 | 0 | `0x0004` | `0x30` | 3 | TRIM | 64 | ARRIVING_TRIM |
| 12208 | `SW_TRIM` | 7 | 4 | 0 | `0x0005` | `0x30` | 3 | TRIM | 64 | BOOTED_TRIM |
| 12536 | `SW_TRIM` | 3 | 5 | 0 | `0x0006` | `0x30` | 3 | TRIM | 64 | BOOTED_TRIM |
| 12553 | `RX_DATA` | 6 | 0 | 0 | `0x0001` | `0x20` | 0 | SYN | 4096 | - |
| 12864 | `SW_TRIM` | 8 | 5 | 0 | `0x0006` | `0x30` | 3 | TRIM | 64 | ARRIVING_TRIM |
| 12886 | `RX_TRIM` | 6 | 2 | 2 | `0x0003` | `0x30` | 3 | TRIM | 64 | - |
| 12886 | `TX_NACK` | 6 | 2 | 2 | `0x0003` | `0x30` | 3 | TRIM | 64 | - |
| 12891 | `RX_TRIM` | 4 | 5 | 1 | `0x0006` | `0x30` | 3 | TRIM | 64 | - |
| 12891 | `TX_NACK` | 4 | 5 | 1 | `0x0006` | `0x30` | 3 | TRIM | 64 | - |
| 13192 | `SW_TRIM` | 2 | 5 | 0 | `0x0006` | `0x30` | 3 | TRIM | 64 | ARRIVING_TRIM |
| 13224 | `RX_TRIM` | 1 | 3 | 3 | `0x0004` | `0x30` | 3 | TRIM | 64 | - |
| 13224 | `TX_NACK` | 1 | 3 | 3 | `0x0004` | `0x30` | 3 | TRIM | 64 | - |
| 13229 | `RX_TRIM` | 7 | 4 | 2 | `0x0005` | `0x30` | 3 | TRIM | 64 | - |
| 13229 | `TX_NACK` | 7 | 4 | 2 | `0x0005` | `0x30` | 3 | TRIM | 64 | - |
| 13519 | `SW_TRIM` | 4 | 3 | 0 | `0x0004` | `0x30` | 3 | TRIM | 64 | BOOTED_TRIM |
