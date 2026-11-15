/*
 * mrc_headers.p4
 * Bit-Exact 64-Byte Base Frame Header Definitions for MRC / UET-PDS (P4_16 v1model / PSA)
 *
 * Wire Layout (60B Header + 4B L2 FCS = 64B Trimmed Frame):
 *   Ethernet (14B) + IPv4 (20B) + UDP (8B) + UET_PDS (18B) = 60B
 *   Trimmed IPv4 totalLen = 46B, UDP len = 26B
 */

#ifndef _MRC_HEADERS_P4_
#define _MRC_HEADERS_P4_

const bit<16> ETHERTYPE_IPV4 = 16w0x0800;
const bit<8>  IPPROTO_UDP    = 8w17;
const bit<16> UDP_PORT_MRC   = 16w4791;

const bit<6> DSCP_MRC_TRIMMABLE = 6w0x20;
const bit<6> DSCP_MRC_TRIMMED   = 6w0x30;

const bit<4> PKT_TYPE_DATA  = 4w0;
const bit<4> PKT_TYPE_ACK   = 4w1;
const bit<4> PKT_TYPE_NACK  = 4w2;
const bit<4> PKT_TYPE_PULL  = 4w3;
const bit<4> PKT_TYPE_PROBE = 4w4;

header ethernet_t {
    bit<48> dstAddr;
    bit<48> srcAddr;
    bit<16> etherType;
}

header ipv4_t {
    bit<4>  version;
    bit<4>  ihl;
    bit<6>  dscp;
    bit<2>  ecn;
    bit<16> totalLen;
    bit<16> identification;
    bit<3>  flags;
    bit<13> fragOffset;
    bit<8>  ttl;
    bit<8>  protocol;
    bit<16> hdrChecksum;
    bit<32> srcAddr;
    bit<32> dstAddr;
}

header udp_t {
    bit<16> srcPort;   // Entropy Value (EV) controlled by REPS / Oblivious / Bitmap
    bit<16> dstPort;   // 4791 (UET/MRC)
    bit<16> len;       // 26B when trimmed
    bit<16> checksum;  // 0x0000 for IPv4/UDP
}

header uet_pds_t {
    bit<4>  pkt_type;     // 0=DATA, 1=ACK/SACK, 2=NACK, 3=PULL, 4=PROBE
    bit<1>  flag_syn;     // 1=0-RTT Ephemeral PDC setup packet
    bit<1>  flag_eom;     // 1=End-of-Message / PDC teardown trigger
    bit<1>  flag_trim;    // 1=Payload stripped by switch (Double-Trim prevention)
    bit<1>  flag_probe;   // 1=PFLD/Sleek probe
    bit<1>  flag_rtx;     // 1=Retransmitted packet
    bit<1>  flag_bts;     // 1=Back-to-Sender reflected trim
    bit<6>  rsvd;
    bit<16> init_pdc_id;  // Initiator PDC ID
    bit<16> tgt_pdc_id;   // Target PDC ID
    bit<32> psn;          // Packet Sequence Number / Ref_EPSN / Pull_No
    bit<32> cumm_ack;     // Cumulative ACK / Start_PSN (when SYN=1)
    bit<16> ev_echo;      // Echoed EV (ACK) or Discarded_EV (NACK)
    bit<4>  trim_hop;     // Switch ID where trimming occurred
    bit<4>  csig;         // 4-bit In-band Congestion Telemetry Signal
    bit<8>  hdr_crc8;     // Header integrity CRC-8 (covers UET_PDS bytes)
}

struct headers_t {
    ethernet_t ethernet;
    ipv4_t     ipv4;
    udp_t      udp;
    uet_pds_t  uet;
}

struct mrc_metadata_t {
    bit<3>  qid;
    bit<1>  trimmable;
    bit<16> ecmp_select;
    bit<9>  ingress_port;
}

#endif /* _MRC_HEADERS_P4_ */
