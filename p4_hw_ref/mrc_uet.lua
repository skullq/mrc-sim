-- mrc_uet.lua
-- Wireshark / tshark Lua Dissector for MRC / UET-PDS (UDP DstPort = 4791)
-- Matches SPEC.md Section 6.2 Bit-Exact 64-Byte Base Frame

local uet_proto = Proto("uet_mrc", "UET / MRC Transport Protocol")

local pkt_types = {
    [0] = "DATA",
    [1] = "ACK/SACK",
    [2] = "NACK",
    [3] = "PULL",
    [4] = "PROBE"
}

local f_pkt_type   = ProtoField.uint8("uet_mrc.pkt_type",   "Packet Type",    base.DEC, pkt_types, 0xF0)
local f_flag_syn   = ProtoField.uint8("uet_mrc.syn",        "SYN",            base.DEC, nil,       0x08)
local f_flag_eom   = ProtoField.uint8("uet_mrc.eom",        "EOM",            base.DEC, nil,       0x04)
local f_flag_trim  = ProtoField.uint8("uet_mrc.trimmed",    "TRIMMED",        base.DEC, nil,       0x02)
local f_flag_probe = ProtoField.uint8("uet_mrc.probe",      "PROBE",          base.DEC, nil,       0x01)
local f_flag_rtx   = ProtoField.uint8("uet_mrc.rtx",        "RTX",            base.DEC, nil,       0x80)
local f_flag_bts   = ProtoField.uint8("uet_mrc.bts",        "BTS",            base.DEC, nil,       0x40)
local f_init_pdc   = ProtoField.uint16("uet_mrc.init_pdc",  "Initiator PDC",  base.DEC)
local f_tgt_pdc    = ProtoField.uint16("uet_mrc.tgt_pdc",   "Target PDC",     base.DEC)
local f_psn        = ProtoField.uint32("uet_mrc.psn",       "PSN / Ref_EPSN", base.DEC)
local f_cumm_ack   = ProtoField.uint32("uet_mrc.cumm_ack",  "Cumm_ACK / Start_PSN", base.DEC)
local f_ev_echo    = ProtoField.uint16("uet_mrc.ev_echo",   "EV_Echo / Bad_EV", base.HEX)
local f_trim_hop   = ProtoField.uint8("uet_mrc.trim_hop",   "Trim Hop",       base.DEC, nil,       0xF0)
local f_csig       = ProtoField.uint8("uet_mrc.csig",       "CSIG",           base.DEC, nil,       0x0F)
local f_hdr_crc8   = ProtoField.uint8("uet_mrc.hdr_crc8",   "Header CRC-8",   base.HEX)
local f_sack_bmp   = ProtoField.uint64("uet_mrc.sack_bitmap", "SACK Bitmap",  base.HEX)

uet_proto.fields = {
    f_pkt_type, f_flag_syn, f_flag_eom, f_flag_trim, f_flag_probe,
    f_flag_rtx, f_flag_bts, f_init_pdc, f_tgt_pdc, f_psn, f_cumm_ack,
    f_ev_echo, f_trim_hop, f_csig, f_hdr_crc8, f_sack_bmp
}

local f_udp_sport = Field.new("udp.srcport")

function uet_proto.dissector(buffer, pinfo, tree)
    if buffer:len() < 18 then return end

    pinfo.cols.protocol = "UET/MRC"

    local subtree = tree:add(uet_proto, buffer(), "UET/MRC PDS Header (18B)")
    local b0 = buffer(0, 1):uint()
    local b1 = buffer(1, 1):uint()
    local ptype = bit.rshift(b0, 4)
    local is_syn   = bit.band(b0, 0x08) ~= 0
    local is_eom   = bit.band(b0, 0x04) ~= 0
    local is_trim  = bit.band(b0, 0x02) ~= 0
    local is_probe = bit.band(b0, 0x01) ~= 0
    local is_rtx   = bit.band(b1, 0x80) ~= 0
    local is_bts   = bit.band(b1, 0x40) ~= 0

    subtree:add(f_pkt_type,   buffer(0, 1))
    subtree:add(f_flag_syn,   buffer(0, 1))
    subtree:add(f_flag_eom,   buffer(0, 1))
    subtree:add(f_flag_trim,  buffer(0, 1))
    subtree:add(f_flag_probe, buffer(0, 1))
    subtree:add(f_flag_rtx,   buffer(1, 1))
    subtree:add(f_flag_bts,   buffer(1, 1))
    subtree:add(f_init_pdc,   buffer(2, 2))
    subtree:add(f_tgt_pdc,    buffer(4, 2))
    subtree:add(f_psn,        buffer(6, 4))
    subtree:add(f_cumm_ack,   buffer(10, 4))
    subtree:add(f_ev_echo,    buffer(14, 2))
    subtree:add(f_trim_hop,   buffer(16, 1))
    subtree:add(f_csig,       buffer(16, 1))
    subtree:add(f_hdr_crc8,   buffer(17, 1))

    local flow_id = buffer(2, 2):uint()
    local psn     = buffer(6, 4):uint()
    local cack    = buffer(10, 4):uint()
    local ev_echo = buffer(14, 2):uint()
    local thop    = bit.rshift(buffer(16, 1):uint(), 4)
    local ev_f    = f_udp_sport()
    local ev      = ev_f and tonumber(tostring(ev_f)) or 0

    if ptype == 1 and buffer:len() >= 26 then
        subtree:add(f_sack_bmp, buffer(18, 8))
    end

    local tag = pkt_types[ptype] or "UNK"
    if ptype == 0 and is_trim then tag = "TRIM" end
    if ptype == 0 and is_rtx  then tag = "RTX"  end

    local flags_str = ""
    if is_syn   then flags_str = flags_str .. " [SYN]"   end
    if is_eom   then flags_str = flags_str .. " [EOM]"   end
    if is_trim  then flags_str = flags_str .. string.format(" [TRIMMED@Hop=%d]", thop) end
    if is_probe then flags_str = flags_str .. " [PROBE]" end
    if is_bts   then flags_str = flags_str .. " [BTS]"   end

    pinfo.cols.info = string.format("[%s] PDC=%d PSN=%d CummACK=%d EV=0x%04x EV_Echo=0x%04x%s",
        tag, flow_id, psn, cack, ev, ev_echo, flags_str)
end

local udp_table = DissectorTable.get("udp.port")
udp_table:add(4791, uet_proto)
