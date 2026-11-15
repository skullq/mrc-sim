#!/usr/bin/env python3
"""
export_hw_vectors.py
Implements TC-10 & SPEC.md Section 6.2 / 6.5:
Converts htsim MRC_TRACE_FILE CSV logs into:
  1. <prefix>_switch_ingress.pcap  (pre-trim full packets, DSCP=0x20)
  2. <prefix>_switch_egress.pcap   (post-switch packets: 64B trimmed DSCP=0x30 & ECN-marked)
  3. <prefix>_end_to_end_full.pcap (chronological full trace)
  4. <prefix>_axi512.tv            (512-bit AXI-Stream tdata/tkeep/tlast golden vectors)
And verifies bit-exact framing (60B header + 4B L2 FCS = 64B trimmed frame).
"""

import argparse
import csv
import struct
from pathlib import Path

PCAP_GLOBAL_HDR = struct.pack("<IHHiIII", 0xA1B2C3D4, 2, 4, 0, 0, 65535, 1)  # LINKTYPE_ETHERNET=1

PKT_TYPE_MAP = {
    "DATA": 0,
    "ACK": 1,
    "NACK": 2,
    "PULL": 3,
    "PROBE": 4,
    "TRIM": 0,
}


def crc8_uet(data: bytes) -> int:
    crc = 0
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = ((crc << 1) ^ 0x07) & 0xFF if (crc & 0x80) else (crc << 1) & 0xFF
    return crc


def ipv4_checksum(hdr: bytes) -> int:
    if len(hdr) % 2 == 1:
        hdr += b"\x00"
    s = sum(struct.unpack("!%dH" % (len(hdr) // 2), hdr))
    while s >> 16:
        s = (s & 0xFFFF) + (s >> 16)
    return (~s) & 0xFFFF


def build_wire_frame(row: dict) -> bytes:
    src_id = int(row["src"]) & 0xFFFF
    dst_id = int(row["dst"]) & 0xFFFF
    flow_id = int(row["flow_id"]) & 0xFFFF
    psn = int(row["psn"]) & 0xFFFFFFFF
    cumm_ack = int(row["cumm_ack"]) & 0xFFFFFFFF
    sack_bmp = int(row["sack_bitmap"], 16) & 0xFFFFFFFFFFFFFFFF
    ev = int(row["ev"], 16) & 0xFFFF
    dscp = int(row["dscp"], 16) & 0x3F
    ecn = int(row["ecn"]) & 0x03
    trimmed = int(row["trimmed"]) & 0x01
    rtx = int(row["rtx"]) & 0x01
    probe = int(row["probe"]) & 0x01
    syn = int(row["syn"]) & 0x01
    eom = int(row["eom"]) & 0x01
    bts = int(row["bts"]) & 0x01
    hop = int(row["hop"]) & 0x0F
    sim_size = int(row["size"])
    ptype = PKT_TYPE_MAP.get(row["pkt_type"], 0)

    # Ethernet (14B)
    dst_mac = bytes([0x02, 0x00, 0x00, 0x00, (dst_id >> 8) & 0xFF, dst_id & 0xFF])
    src_mac = bytes([0x02, 0x00, 0x00, 0x00, (src_id >> 8) & 0xFF, src_id & 0xFF])
    eth = dst_mac + src_mac + struct.pack("!H", 0x0800)

    # Payload length on wire
    if trimmed or ptype in (2, 3, 4):
        payload = b""
    elif ptype == 1:
        payload = struct.pack("!Q", sack_bmp)  # 8B SACK bitmap
    else:
        plen = max(0, min(sim_size, 4096))
        payload = (b"\xAA\x55\xDE\xAD" * ((plen + 3) // 4))[:plen]

    # UET_PDS (18B)
    b0 = ((ptype & 0xF) << 4) | (syn << 3) | (eom << 2) | (trimmed << 1) | probe
    b1 = (rtx << 7) | (bts << 6)
    b16 = ((hop & 0xF) << 4) | (0x3 if ecn == 3 else 0x0)
    uet_wo_crc = struct.pack(
        "!BBHHIIHB",
        b0, b1, flow_id, flow_id, psn, cumm_ack, ev, b16
    )
    crc8 = crc8_uet(uet_wo_crc)
    uet = uet_wo_crc + struct.pack("!B", crc8)
    assert len(uet) == 18

    udp_len = 8 + len(uet) + len(payload)
    udp = struct.pack("!HHHH", ev, 4791, udp_len, 0)

    ip_len = 20 + udp_len
    tos = (dscp << 2) | ecn
    src_ip = (10 << 24) | src_id
    dst_ip = (10 << 24) | dst_id
    ip_wo_csum = struct.pack(
        "!BBHHHBBHII",
        0x45, tos, ip_len, psn & 0xFFFF, 0x4000, 64, 17, 0, src_ip, dst_ip
    )
    csum = ipv4_checksum(ip_wo_csum)
    ip = ip_wo_csum[:10] + struct.pack("!H", csum) + ip_wo_csum[12:]

    frame_wo_fcs = eth + ip + udp + uet + payload
    if trimmed:
        assert len(frame_wo_fcs) == 60, f"Trimmed header must be 60B (64B w/ FCS), got {len(frame_wo_fcs)}"
        assert ip_len == 46 and udp_len == 26
    return frame_wo_fcs


def write_pcap(path: Path, packets: list[tuple[int, bytes]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        f.write(PCAP_GLOBAL_HDR)
        for ts_ns, frame in packets:
            ts_sec = ts_ns // 1_000_000_000
            ts_usec = (ts_ns % 1_000_000_000) // 1000
            pkt_hdr = struct.pack("<IIII", ts_sec, ts_usec, len(frame), len(frame))
            f.write(pkt_hdr)
            f.write(frame)


def write_axi512_tv(path: Path, packets: list[tuple[int, bytes]], max_pkts: int = 64) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    beats = 0
    with path.open("w") as f:
        f.write("# AXI-Stream 512-bit Golden Vectors (pkt_idx beat_idx tvalid tlast tkeep_hex tdata_hex)\n")
        for p_idx, (_, frame) in enumerate(packets[:max_pkts]):
            for b_idx, off in enumerate(range(0, len(frame), 64)):
                chunk = frame[off:off + 64]
                tlast = 1 if (off + 64 >= len(frame)) else 0
                tkeep = (1 << len(chunk)) - 1
                padded = chunk.ljust(64, b"\x00")
                f.write(f"{p_idx} {b_idx} 1 {tlast} 0x{tkeep:016x} 0x{padded.hex()}\n")
                beats += 1
    return beats


def export_vectors(trace_csv: Path, out_prefix: Path) -> dict:
    ingress_pkts = []
    egress_pkts = []
    full_pkts = []
    trimmed_verified = 0

    with trace_csv.open("r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ts_ns = int(row["ts_ns"])
            frame = build_wire_frame(row)
            full_pkts.append((ts_ns, frame))
            ev = row["event"]
            if ev in ("TX_DATA", "TX_RTX"):
                ingress_pkts.append((ts_ns, frame))
            elif ev in ("SW_TRIM", "SW_ECN", "SW_BTS", "RX_DATA", "RX_TRIM"):
                egress_pkts.append((ts_ns, frame))
            if row["trimmed"] == "1" and row["pkt_type"] in ("DATA", "TRIM"):
                trimmed_verified += 1

    write_pcap(Path(f"{out_prefix}_switch_ingress.pcap"), ingress_pkts)
    write_pcap(Path(f"{out_prefix}_switch_egress.pcap"), egress_pkts)
    write_pcap(Path(f"{out_prefix}_end_to_end_full.pcap"), full_pkts)
    tv_beats = write_axi512_tv(Path(f"{out_prefix}_axi512.tv"), full_pkts)

    return {
        "ingress_count": len(ingress_pkts),
        "egress_count": len(egress_pkts),
        "full_count": len(full_pkts),
        "trimmed_64b_verified": trimmed_verified,
        "axi512_beats": tv_beats,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("trace_csv", type=Path)
    ap.add_argument("-p", "--prefix", type=Path, required=True)
    args = ap.parse_args()
    stats = export_vectors(args.trace_csv, args.prefix)
    print(f"[TC-10 Export] {args.prefix}: {stats}")


if __name__ == "__main__":
    main()
