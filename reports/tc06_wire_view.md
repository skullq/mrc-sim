# Wire View Report: `tc06_trace.csv`

## 1. Event Counters
| Event | Count |
| :--- | ---: |
| `RX_ACK` | 559 |
| `RX_DATA` | 1048 |
| `RX_NACK` | 316 |
| `RX_PULL` | 415 |
| `RX_TRIM` | 316 |
| `SW_ECN` | 435 |
| `SW_TRIM` | 316 |
| `TX_DATA` | 1048 |
| `TX_NACK` | 316 |
| `TX_RTX` | 316 |

- **Unique Entropy Values (EVs) observed**: `55`
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
| 7587 | `SW_ECN` | 8 | 4 | 0 | `0x0005` | `0x20` | 3 | - | 4096 | - |
| 7932 | `SW_ECN` | 3 | 1 | 0 | `0x0002` | `0x20` | 3 | - | 4096 | - |
| 7966 | `RX_DATA` | 1 | 0 | 0 | `0x0001` | `0x20` | 0 | SYN | 4096 | - |
| 8293 | `RX_DATA` | 3 | 0 | 0 | `0x0001` | `0x20` | 0 | SYN | 4096 | - |
| 8570 | `SW_ECN` | 1 | 5 | 0 | `0x0006` | `0x20` | 3 | - | 4096 | - |
| 8587 | `SW_ECN` | 5 | 3 | 0 | `0x0004` | `0x20` | 3 | - | 4096 | - |
| 8621 | `RX_DATA` | 7 | 0 | 0 | `0x0001` | `0x20` | 0 | SYN | 4096 | - |
| 8898 | `SW_ECN` | 6 | 4 | 0 | `0x0005` | `0x20` | 3 | - | 4096 | - |
| 9276 | `RX_DATA` | 8 | 0 | 0 | `0x0001` | `0x20` | 0 | SYN | 4096 | - |
| 9604 | `RX_DATA` | 5 | 0 | 0 | `0x0001` | `0x20` | 0 | SYN | 4096 | - |
| 10587 | `RX_DATA` | 4 | 0 | 0 | `0x0001` | `0x20` | 0 | SYN | 4096 | - |
| 10915 | `RX_DATA` | 2 | 0 | 0 | `0x0001` | `0x20` | 0 | SYN | 4096 | - |
| 11847 | `SW_TRIM` | 6 | 16 | 0 | `0x0001` | `0x30` | 0 | TRIM | 64 | ARRIVING_TRIM |
| 12175 | `SW_TRIM` | 4 | 17 | 0 | `0x000c` | `0x30` | 0 | TRIM | 64 | BOOTED_TRIM |
| 12502 | `SW_TRIM` | 2 | 16 | 0 | `0x0001` | `0x30` | 0 | TRIM | 64 | ARRIVING_TRIM |
| 12502 | `SW_TRIM` | 5 | 17 | 0 | `0x000b` | `0x30` | 0 | TRIM | 64 | BOOTED_TRIM |
| 12830 | `SW_TRIM` | 6 | 20 | 0 | `0x0007` | `0x30` | 0 | TRIM | 64 | ARRIVING_TRIM |
| 12847 | `SW_TRIM` | 6 | 17 | 0 | `0x000e` | `0x30` | 0 | TRIM | 64 | BOOTED_TRIM |
| 13158 | `SW_TRIM` | 6 | 21 | 0 | `0x0008` | `0x30` | 0 | TRIM | 64 | ARRIVING_TRIM |
| 13175 | `SW_TRIM` | 3 | 15 | 0 | `0x000a` | `0x30` | 3 | TRIM | 64 | BOOTED_TRIM |
| 13175 | `SW_TRIM` | 7 | 14 | 0 | `0x000a` | `0x30` | 0 | TRIM | 64 | ARRIVING_TRIM |
| 13485 | `SW_TRIM` | 3 | 19 | 0 | `0x000d` | `0x30` | 0 | TRIM | 64 | BOOTED_TRIM |
| 13502 | `SW_TRIM` | 7 | 17 | 0 | `0x0004` | `0x30` | 0 | TRIM | 64 | BOOTED_TRIM |
| 13502 | `SW_TRIM` | 2 | 19 | 0 | `0x0004` | `0x30` | 3 | TRIM | 64 | BOOTED_TRIM |
| 13512 | `SW_TRIM` | 8 | 13 | 0 | `0x000f` | `0x30` | 3 | TRIM | 64 | BOOTED_TRIM |
| 13813 | `SW_TRIM` | 1 | 19 | 0 | `0x0000` | `0x30` | 0 | TRIM | 64 | BOOTED_TRIM |
| 13830 | `SW_TRIM` | 1 | 10 | 0 | `0x0006` | `0x30` | 3 | TRIM | 64 | BOOTED_TRIM |
| 13830 | `SW_TRIM` | 7 | 18 | 0 | `0x0003` | `0x30` | 3 | TRIM | 64 | BOOTED_TRIM |
| 13850 | `SW_TRIM` | 8 | 14 | 0 | `0x0007` | `0x30` | 3 | TRIM | 64 | BOOTED_TRIM |
| 13996 | `RX_ACK` | 1 | 0 | 1 | `0x0001` | `0x30` | 0 | - | 64 | - |
| 14001 | `RX_PULL` | 1 | 100000016 | 0 | `0x0001` | `0x30` | 0 | - | 64 | - |
| 14141 | `SW_TRIM` | 8 | 22 | 0 | `0x0008` | `0x30` | 0 | TRIM | 64 | ARRIVING_TRIM |
