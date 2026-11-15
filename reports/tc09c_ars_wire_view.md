# Wire View Report: `tc09c_ars_trace.csv`

## 1. Event Counters
| Event | Count |
| :--- | ---: |
| `RX_ACK` | 705 |
| `RX_DATA` | 1049 |
| `RX_NACK` | 300 |
| `RX_TRIM` | 300 |
| `SW_ECN` | 572 |
| `SW_TRIM` | 300 |
| `TX_DATA` | 1048 |
| `TX_NACK` | 300 |
| `TX_RTX` | 301 |

- **Unique Entropy Values (EVs) observed**: `128`
- **0-RTT SYN observed**: `True` | **EOM observed**: `True`

## 2. Key Packet Timeline (Wire View)
| Time (ns) | Event | Flow | PSN | CummACK | EV | DSCP | ECN | Flags | Size (B) | Extra |
| ---: | :--- | ---: | ---: | ---: | :--- | :--- | ---: | :--- | ---: | :--- |
| 0 | `TX_DATA` | 1 | 0 | 0 | `0xe278` | `0x20` | 0 | SYN | 4096 | - |
| 0 | `TX_DATA` | 2 | 0 | 0 | `0x1f0a` | `0x20` | 0 | SYN | 4096 | - |
| 0 | `TX_DATA` | 3 | 0 | 0 | `0x4902` | `0x20` | 0 | SYN | 4096 | - |
| 0 | `TX_DATA` | 4 | 0 | 0 | `0x7275` | `0x20` | 0 | SYN | 4096 | - |
| 0 | `TX_DATA` | 5 | 0 | 0 | `0xf3a3` | `0x20` | 0 | SYN | 4096 | - |
| 0 | `TX_DATA` | 6 | 0 | 0 | `0x8c78` | `0x20` | 0 | SYN | 4096 | - |
| 0 | `TX_DATA` | 7 | 0 | 0 | `0xdeda` | `0x20` | 0 | SYN | 4096 | - |
| 0 | `TX_DATA` | 8 | 0 | 0 | `0x7205` | `0x20` | 0 | SYN | 4096 | - |
| 7966 | `RX_DATA` | 1 | 0 | 0 | `0xe278` | `0x20` | 0 | SYN | 4096 | - |
| 8621 | `RX_DATA` | 5 | 0 | 0 | `0xf3a3` | `0x20` | 0 | SYN | 4096 | - |
| 9225 | `SW_ECN` | 1 | 6 | 0 | `0xe27e` | `0x20` | 3 | - | 4096 | ECNQueue |
| 9276 | `RX_DATA` | 7 | 0 | 0 | `0xdeda` | `0x20` | 0 | SYN | 4096 | - |
| 9553 | `SW_ECN` | 5 | 7 | 0 | `0xf3a4` | `0x20` | 3 | - | 4096 | ECNQueue |
| 9881 | `SW_ECN` | 4 | 4 | 0 | `0x7271` | `0x20` | 3 | - | 4096 | ECNQueue |
| 9932 | `RX_DATA` | 2 | 0 | 0 | `0x1f0a` | `0x20` | 0 | SYN | 4096 | - |
| 10208 | `SW_ECN` | 6 | 8 | 0 | `0x8c70` | `0x20` | 3 | - | 4096 | ECNQueue |
| 10208 | `SW_ECN` | 8 | 5 | 0 | `0x7200` | `0x20` | 3 | - | 4096 | ECNQueue |
| 10587 | `RX_DATA` | 3 | 0 | 0 | `0x4902` | `0x20` | 0 | SYN | 4096 | - |
| 11242 | `RX_DATA` | 6 | 0 | 0 | `0x8c78` | `0x20` | 0 | SYN | 4096 | - |
| 11881 | `SW_TRIM` | 2 | 5 | 0 | `0x1f0f` | `0x30` | 3 | TRIM | 64 | BOOTED_TRIM |
| 12208 | `SW_TRIM` | 8 | 2 | 0 | `0x7207` | `0x30` | 3 | TRIM | 64 | ARRIVING_TRIM |
| 12536 | `SW_TRIM` | 6 | 4 | 0 | `0x8c7c` | `0x30` | 3 | TRIM | 64 | ARRIVING_TRIM |
| 12536 | `SW_TRIM` | 7 | 4 | 0 | `0xdede` | `0x30` | 3 | TRIM | 64 | ARRIVING_TRIM |
| 12553 | `RX_DATA` | 4 | 0 | 0 | `0x7275` | `0x20` | 0 | SYN | 4096 | - |
| 12864 | `SW_TRIM` | 3 | 2 | 0 | `0x4900` | `0x30` | 3 | TRIM | 64 | ARRIVING_TRIM |
| 13192 | `SW_TRIM` | 5 | 5 | 0 | `0xf3a6` | `0x30` | 3 | TRIM | 64 | BOOTED_TRIM |
| 13214 | `RX_TRIM` | 2 | 5 | 3 | `0x1f0f` | `0x30` | 3 | TRIM | 64 | - |
| 13214 | `TX_NACK` | 2 | 5 | 3 | `0x1f0f` | `0x30` | 3 | TRIM | 64 | - |
| 13219 | `RX_TRIM` | 8 | 2 | 0 | `0x7207` | `0x30` | 3 | TRIM | 64 | - |
| 13219 | `TX_NACK` | 8 | 2 | 0 | `0x7207` | `0x30` | 3 | TRIM | 64 | - |
| 13519 | `SW_TRIM` | 6 | 2 | 0 | `0x8c7a` | `0x30` | 3 | TRIM | 64 | ARRIVING_TRIM |
| 13552 | `RX_TRIM` | 6 | 4 | 1 | `0x8c7c` | `0x30` | 3 | TRIM | 64 | - |
| 13552 | `TX_NACK` | 6 | 4 | 1 | `0x8c7c` | `0x30` | 3 | TRIM | 64 | - |
| 13557 | `RX_TRIM` | 7 | 4 | 3 | `0xdede` | `0x30` | 3 | TRIM | 64 | - |
| 13557 | `TX_NACK` | 7 | 4 | 3 | `0xdede` | `0x30` | 3 | TRIM | 64 | - |
| 13847 | `SW_TRIM` | 4 | 7 | 0 | `0x7272` | `0x30` | 3 | TRIM | 64 | BOOTED_TRIM |
| 13884 | `RX_DATA` | 8 | 0 | 0 | `0x7205` | `0x20` | 0 | SYN | 4096 | - |
| 13889 | `RX_TRIM` | 3 | 2 | 1 | `0x4900` | `0x30` | 3 | TRIM | 64 | - |
| 13889 | `TX_NACK` | 3 | 2 | 1 | `0x4900` | `0x30` | 3 | TRIM | 64 | - |
| 13996 | `RX_ACK` | 1 | 0 | 1 | `0xe278` | `0x30` | 0 | - | 64 | - |
