# MRC Simulation Verification Summary (`TC-01 ~ TC-10`)

| Test ID | Scenario | Status | Key Metrics |
| :--- | :--- | :---: | :--- |
| **TC-01** | 0-RTT Ephemeral PDC & REPS Lifecycle | **PASS** | New=66, UniqueEVs=16, SYN=True, EOM=True |
| **TC-02** | 8:1 Incast Trimming, NACK & REPS Reroute | **PASS** | SW_TRIM=306, TX_NACK=306, TX_RTX=308 |
| **TC-03** | RTX-of-RTX & Tail/EOM Recovery | **PASS** | SW_TRIM=643, TX_RTX=671, EOM=True |
| **TC-04** | 4-Algo Multipath Comparison | **PASS** | oblivious:Rtx=0, bitmap:Rtx=0, reps:Rtx=0, mixed:Rtx=0 |
| **TC-05** | Blackhole + REPS Freezing + PFLD/Sleek | **PASS** | TX_PROBE=7, sleek_pkts=134, Rtx=131 |
| **TC-06** | RCCC Receiver-Driven Pull Pacing | **PASS** | Pulls=415, SW_TRIM=316 |
| **TC-07** | SMaRTT ECN+Delay / QuickAdapt / FastIncrease | **PASS** | SW_ECN=213, SW_TRIM=144, ACKs=899 |
| **TC-08** | Full-Stack Hybrid All-to-All (240 flows, -failed 1) | **PASS** | New=4080, Rtx=198, Pulls=7827 |
| **TC-09** | SONiC/SAI Corner Cases & Switch-Centric (ARS/BTS) | **PASS** | 9a_DROPDTT=236, 9b_TRIM=295, 9c_ARS_Rtx=301, 9d_BTS=555/Bounced=555 |
| **TC-10** | P4/RTL Bit-Exact .pcap & AXI512 .tv Golden Vectors | **PASS** | tc02_full=4912 pkts, 64B_trimmed_verified=612, axi512_beats=4160 |
