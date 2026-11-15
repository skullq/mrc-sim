# Wire View Report: `tc03_trace.csv`

## 1. Event Counters
| Event | Count |
| :--- | ---: |
| `RX_ACK` | 1318 |
| `RX_DATA` | 1600 |
| `RX_NACK` | 635 |
| `RX_TRIM` | 635 |
| `SW_ECN` | 1229 |
| `SW_TRIM` | 643 |
| `TX_DATA` | 1572 |
| `TX_NACK` | 635 |
| `TX_RTX` | 671 |

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
| 6932 | `SW_ECN` | 3 | 3 | 0 | `0x0004` | `0x20` | 3 | - | 4096 | ECNQueue |
| 6932 | `SW_ECN` | 2 | 2 | 0 | `0x0003` | `0x20` | 3 | - | 4096 | ECNQueue |
| 7259 | `SW_ECN` | 8 | 2 | 0 | `0x0003` | `0x20` | 3 | - | 4096 | ECNQueue |
| 7259 | `SW_ECN` | 9 | 3 | 0 | `0x0004` | `0x20` | 3 | - | 4096 | ECNQueue |
| 7587 | `SW_ECN` | 11 | 1 | 0 | `0x0002` | `0x20` | 3 | - | 4096 | ECNQueue |
| 7966 | `RX_DATA` | 1 | 0 | 0 | `0x0001` | `0x20` | 0 | SYN | 4096 | - |
| 8293 | `RX_DATA` | 3 | 0 | 0 | `0x0001` | `0x20` | 0 | SYN | 4096 | - |
| 8621 | `RX_DATA` | 7 | 0 | 0 | `0x0001` | `0x20` | 0 | SYN | 4096 | - |
| 8949 | `RX_DATA` | 5 | 0 | 0 | `0x0001` | `0x20` | 0 | SYN | 4096 | - |
| 9276 | `RX_DATA` | 12 | 0 | 0 | `0x0001` | `0x20` | 0 | SYN | 4096 | - |
| 9587 | `SW_TRIM` | 10 | 1 | 0 | `0x0002` | `0x30` | 0 | TRIM | 64 | BOOTED_TRIM |
| 9604 | `RX_DATA` | 2 | 0 | 0 | `0x0001` | `0x20` | 0 | SYN | 4096 | - |
| 9915 | `SW_TRIM` | 8 | 3 | 0 | `0x0004` | `0x30` | 0 | TRIM | 64 | ARRIVING_TRIM |
| 9932 | `RX_DATA` | 10 | 0 | 0 | `0x0001` | `0x20` | 0 | SYN | 4096 | - |
| 10242 | `SW_TRIM` | 3 | 1 | 0 | `0x0002` | `0x30` | 0 | TRIM | 64 | ARRIVING_TRIM |
| 10242 | `SW_TRIM` | 4 | 2 | 0 | `0x0003` | `0x30` | 0 | TRIM | 64 | ARRIVING_TRIM |
| 10259 | `RX_DATA` | 9 | 0 | 0 | `0x0001` | `0x20` | 0 | SYN | 4096 | - |
| 10570 | `SW_TRIM` | 12 | 3 | 0 | `0x0004` | `0x30` | 0 | TRIM | 64 | BOOTED_TRIM |
| 10587 | `RX_DATA` | 8 | 0 | 0 | `0x0001` | `0x20` | 0 | SYN | 4096 | - |
| 10898 | `SW_TRIM` | 6 | 0 | 0 | `0x0001` | `0x30` | 0 | TRIM | 64 | ARRIVING_TRIM |
| 10920 | `RX_TRIM` | 10 | 1 | 1 | `0x0002` | `0x30` | 0 | TRIM | 64 | - |
| 10920 | `TX_NACK` | 10 | 1 | 1 | `0x0002` | `0x30` | 0 | TRIM | 64 | - |
| 10925 | `RX_TRIM` | 8 | 3 | 1 | `0x0004` | `0x30` | 0 | TRIM | 64 | - |
| 10925 | `TX_NACK` | 8 | 3 | 1 | `0x0004` | `0x30` | 0 | TRIM | 64 | - |
| 11225 | `SW_TRIM` | 2 | 3 | 0 | `0x0004` | `0x30` | 3 | TRIM | 64 | BOOTED_TRIM |
| 11258 | `RX_TRIM` | 3 | 1 | 1 | `0x0002` | `0x30` | 0 | TRIM | 64 | - |
| 11258 | `TX_NACK` | 3 | 1 | 1 | `0x0002` | `0x30` | 0 | TRIM | 64 | - |
| 11263 | `RX_TRIM` | 4 | 2 | 0 | `0x0003` | `0x30` | 0 | TRIM | 64 | - |
