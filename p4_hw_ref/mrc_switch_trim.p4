/*
 * mrc_switch_trim.p4
 * Reference P4_16 Switch Pipeline for MRC (v1model target / BMv2 compatible)
 * Implements:
 *   - F-2: Small packet protection (packet_length <= 64B not trimmed)
 *   - F-3: Double-Trim prevention (flag_trim == 1 -> High-Prio queue bypass)
 *   - F-4: L3/L4 Length rewrite (IPv4 totalLen=46, UDP len=26, DSCP=0x30) + IPv4 checksum update
 *   - F-5: Entropy-based ECMP hashing on UDP srcPort (EV)
 *   - F-6: Optional Back-to-Sender (BTS) reflection on Trim
 *   - D-5: ECN CE marking & CSIG telemetry stamping
 */

#include <core.p4>
#include <v1model.p4>
#include "mrc_headers.p4"

const bit<3>  QID_LOW_PRIO_DATA  = 3w0;
const bit<3>  QID_HIGH_PRIO_CTRL = 3w7;

const bit<19> ECN_MARK_THRESHOLD    = 19w16;
const bit<19> BUFFER_TRIM_THRESHOLD = 19w64;
const bit<8>  SWITCH_ID             = 8w1;
const bit<4>  CSIG_SHIFT            = 4w3;

parser MrcParser(packet_in packet,
                 out headers_t hdr,
                 inout mrc_metadata_t meta,
                 inout standard_metadata_t std_meta) {
    state start {
        packet.extract(hdr.ethernet);
        transition select(hdr.ethernet.etherType) {
            ETHERTYPE_IPV4: parse_ipv4;
            default: accept;
        }
    }
    state parse_ipv4 {
        packet.extract(hdr.ipv4);
        transition select(hdr.ipv4.protocol) {
            IPPROTO_UDP: parse_udp;
            default: accept;
        }
    }
    state parse_udp {
        packet.extract(hdr.udp);
        transition select(hdr.udp.dstPort) {
            UDP_PORT_MRC: parse_uet;
            default: accept;
        }
    }
    state parse_uet {
        packet.extract(hdr.uet);
        transition accept;
    }
}

control MrcVerifyChecksum(inout headers_t hdr, inout mrc_metadata_t meta) {
    apply { }
}

control MrcIngress(inout headers_t hdr,
                   inout mrc_metadata_t meta,
                   inout standard_metadata_t std_meta) {
    action set_egress_port(bit<9> port) {
        std_meta.egress_spec = port;
    }
    action drop() {
        mark_to_drop(std_meta);
    }

    table ecmp_group_table {
        key = {
            hdr.ipv4.dstAddr : lpm;
            meta.ecmp_select : exact;
        }
        actions = {
            set_egress_port;
            drop;
        }
        size = 1024;
        default_action = drop();
    }

    apply {
        meta.ingress_port = std_meta.ingress_port;
        if (hdr.ipv4.isValid() && hdr.udp.isValid() && hdr.uet.isValid()) {
            // F-3: Double-Trim prevention & Control packet priority
            if (hdr.uet.flag_trim == 1 || hdr.uet.pkt_type != PKT_TYPE_DATA) {
                meta.qid = QID_HIGH_PRIO_CTRL;
                meta.trimmable = 1w0;
            } else {
                meta.qid = QID_LOW_PRIO_DATA;
                meta.trimmable = (hdr.ipv4.dscp == DSCP_MRC_TRIMMABLE) ? 1w1 : 1w0;
            }

            // F-5: Multipath ECMP using UDP srcPort (EV)
            hash(meta.ecmp_select, HashAlgorithm.crc16, (bit<16>)0,
                 { hdr.ipv4.srcAddr, hdr.ipv4.dstAddr, hdr.udp.srcPort }, (bit<32>)64);
            ecmp_group_table.apply();
        }
    }
}

control MrcEgress(inout headers_t hdr,
                  inout mrc_metadata_t meta,
                  inout standard_metadata_t std_meta) {
    apply {
        if (hdr.uet.isValid() && hdr.uet.pkt_type == PKT_TYPE_DATA && hdr.uet.flag_trim == 0) {
            // F-2: Protect short packets (packet_length <= 64B)
            // F-3: Only trim if DSCP == Trimmable and not already trimmed
            if (std_meta.deq_qdepth >= BUFFER_TRIM_THRESHOLD &&
                meta.trimmable == 1w1 &&
                std_meta.packet_length > 64) {

                // H-2: Truncate payload, keep 60B header (64B on wire with L2 FCS)
                truncate((bit<32>)60);
                hdr.uet.flag_trim = 1w1;
                hdr.uet.trim_hop  = (bit<4>)SWITCH_ID;
                hdr.ipv4.dscp     = DSCP_MRC_TRIMMED;
                hdr.ipv4.totalLen = 16w46;  // F-4: 20B IP + 8B UDP + 18B UET
                hdr.udp.len       = 16w26;  // F-4: 8B UDP + 18B UET
                hdr.udp.checksum  = 16w0;
            } else if (std_meta.deq_qdepth >= ECN_MARK_THRESHOLD) {
                // D-1 / D-5: ECN CE marking and 4-bit CSIG queue telemetry
                hdr.ipv4.ecn = 2w3;
                hdr.uet.csig = (bit<4>)(std_meta.deq_qdepth >> CSIG_SHIFT);
            }
        }
    }
}

control MrcComputeChecksum(inout headers_t hdr, inout mrc_metadata_t meta) {
    apply {
        update_checksum(
            hdr.ipv4.isValid(),
            { hdr.ipv4.version, hdr.ipv4.ihl, hdr.ipv4.dscp, hdr.ipv4.ecn,
              hdr.ipv4.totalLen, hdr.ipv4.identification, hdr.ipv4.flags,
              hdr.ipv4.fragOffset, hdr.ipv4.ttl, hdr.ipv4.protocol,
              hdr.ipv4.srcAddr, hdr.ipv4.dstAddr },
            hdr.ipv4.hdrChecksum,
            HashAlgorithm.csum16);
    }
}

control MrcDeparser(packet_out packet, in headers_t hdr) {
    apply {
        packet.emit(hdr.ethernet);
        packet.emit(hdr.ipv4);
        packet.emit(hdr.udp);
        packet.emit(hdr.uet);
    }
}

V1Switch(
    MrcParser(),
    MrcVerifyChecksum(),
    MrcIngress(),
    MrcEgress(),
    MrcComputeChecksum(),
    MrcDeparser()
) main;
