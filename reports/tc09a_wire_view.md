# Wire View Report: `tc09a_trace.csv`

## 1. Event Counters
| Event | Count |
| :--- | ---: |
| `RX_ACK` | 439048 |
| `RX_DATA` | 2168 |
| `RX_NACK` | 1126 |
| `RX_TRIM` | 1126 |
| `SW_DROPDTT` | 236 |
| `SW_ECN` | 19172 |
| `SW_SKIP_SHORT_TRIM` | 31304 |
| `SW_TRIM` | 1993 |
| `TX_DATA` | 1233 |
| `TX_NACK` | 1126 |
| `TX_PROBE` | 469860 |
| `TX_RTX` | 3014 |

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
| 6604 | `SW_DROPDTT` | 14 | 5 | 0 | `0x0006` | `0x30` | 0 | TRIM | 64 | F1_DROPDTT_HIGHQ |
| 6932 | `SW_ECN` | 9 | 1 | 0 | `0x0002` | `0x20` | 3 | - | 4096 | ECNQueue |
| 6932 | `SW_ECN` | 7 | 2 | 0 | `0x0003` | `0x20` | 3 | - | 4096 | ECNQueue |
| 6932 | `SW_TRIM` | 1 | 0 | 0 | `0x0001` | `0x30` | 0 | TRIM | 64 | ARRIVING_TRIM |
| 6932 | `SW_TRIM` | 3 | 0 | 0 | `0x0001` | `0x30` | 0 | TRIM | 64 | ARRIVING_TRIM |
| 6932 | `SW_DROPDTT` | 3 | 0 | 0 | `0x0001` | `0x30` | 0 | TRIM | 64 | F1_DROPDTT_HIGHQ |
| 7259 | `SW_ECN` | 8 | 2 | 0 | `0x0003` | `0x20` | 3 | - | 4096 | ECNQueue |
| 7259 | `SW_ECN` | 9 | 3 | 0 | `0x0004` | `0x20` | 3 | - | 4096 | ECNQueue |
| 7259 | `SW_TRIM` | 13 | 6 | 0 | `0x0007` | `0x30` | 0 | TRIM | 64 | ARRIVING_TRIM |
| 7587 | `SW_TRIM` | 2 | 1 | 0 | `0x0002` | `0x30` | 0 | TRIM | 64 | ARRIVING_TRIM |
| 7609 | `RX_TRIM` | 13 | 7 | 4 | `0x0008` | `0x30` | 0 | TRIM | 64 | - |
| 7609 | `TX_NACK` | 13 | 7 | 4 | `0x0008` | `0x30` | 0 | TRIM | 64 | - |
| 7915 | `SW_TRIM` | 7 | 0 | 0 | `0x0001` | `0x30` | 0 | TRIM | 64 | BOOTED_TRIM |
| 7942 | `RX_TRIM` | 1 | 0 | 0 | `0x0001` | `0x30` | 0 | TRIM | 64 | - |
| 7942 | `TX_NACK` | 1 | 0 | 0 | `0x0001` | `0x30` | 0 | TRIM | 64 | - |
| 8242 | `SW_TRIM` | 14 | 6 | 0 | `0x0007` | `0x30` | 0 | TRIM | 64 | ARRIVING_TRIM |
| 8275 | `RX_TRIM` | 13 | 6 | 5 | `0x0007` | `0x30` | 0 | TRIM | 64 | - |
| 8275 | `TX_NACK` | 13 | 6 | 5 | `0x0007` | `0x30` | 0 | TRIM | 64 | - |
| 8570 | `SW_TRIM` | 14 | 8 | 0 | `0x0009` | `0x30` | 0 | TRIM | 64 | BOOTED_TRIM |
| 8608 | `RX_TRIM` | 2 | 1 | 0 | `0x0002` | `0x30` | 0 | TRIM | 64 | - |
| 8608 | `TX_NACK` | 2 | 1 | 0 | `0x0002` | `0x30` | 0 | TRIM | 64 | - |
