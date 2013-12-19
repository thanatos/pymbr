import struct as _struct

import six as _six


if not hasattr(_six, 'indexbytes'):
    import sys as _sys
    if _sys.version_info.major == 2:
        def _indexbytes(b, idx):
            return ord(b[idx])
    else:
        def _indexbytes(b, idx):
            return b[idx]
    _six.indexbytes = _indexbytes


PARTITION_TYPE_LINUX = 0x83


class CylinderHeadSector(object):
    def __init__(self, cylinder, head, sector):
        self.cylinder = cylinder
        self.head = head
        self.sector = sector


class Partition(object):
    def __init__(
            self,
            bootable,
            chs_first_sector, chs_last_sector,
            partition_type, lba_first_sector, number_of_sectors):
        self.bootable = bootable
        self.chs_first_sector = chs_first_sector
        self.chs_last_sector = chs_last_sector
        self.partition_type = partition_type
        self.lba_first_sector = lba_first_sector
        self.number_of_sectors = number_of_sectors


def decode_chs_bytes(chs_bytes):
    h = _six.indexbytes(chs_bytes, 0)
    s = _six.indexbytes(chs_bytes, 1)
    c = _six.indexbytes(chs_bytes, 2)
    # The high 2 bits (bits 9 & 10) of the cylinder get stored in the sector's
    # upper 2 bits. The sector is only 6 bits long.
    c |= s >> 6
    s &= 0x3f
    return CylinderHeadSector(c, h, s)


def encode_chs_bytes(chs):
    pieces = [
        _six.int2byte(chs.head),
        _six.int2byte((chs.sector & 0x3f) | ((chs.cylinder >> 2) & 0xc0)),
        _six.int2byte(chs.cylinder & 0xff),
    ]
    return b''.join(pieces)


def decode_partition(partition_data):
    assert len(partition_data) == 16
    status = _six.indexbytes(partition_data, 0)
    assert status in (0, 0x80)
    bootable = status == 0x80
    chs_first_sector = decode_chs_bytes(partition_data[1:4])
    partition_type = _six.indexbytes(partition_data, 4)
    chs_last_sector = decode_chs_bytes(partition_data[5:8])
    lba_data = partition_data[8:]
    lba_first_sector, num_sectors = (
        _struct.unpack_from('<II', partition_data, 8))
    return Partition(
        bootable,
        chs_first_sector, chs_last_sector,
        partition_type,
        lba_first_sector, num_sectors)


def encode_partition(partition):
    lba_data = _struct.pack(
        '<II', partition.lba_first_sector, partition.number_of_sectors)
    parts = [
        b'\x80' if partition.bootable else b'\x00',
        encode_chs_bytes(partition.chs_first_sector),
        _six.int2byte(partition.partition_type),
        encode_chs_bytes(partition.chs_last_sector),
        lba_data,
    ]
    return b''.join(parts)


def decode_mbr(data):
    if not (
            _six.indexbytes(data, -2) == 0x55
            and _six.indexbytes(data, -1) == 0xaa):
        raise IOError('MBR signature not found.')
    partition_table = data[0x1be:0x1fe]
    partitions = []
    for idx in _six.moves.xrange(4):
        partition_data = partition_table[idx*16:idx*16+16]
        partitions.append(decode_partition(partition_data))

    return partitions


def encode_mbr(partitions):
    assert len(partitions) == 4
    partition_data = []
    for partition in partitions:
        if partition is None:
            partition_data.append(b'\x00' * 16)
        else:
            partition_data.append(encode_partition(partition))

    preamble = b'\x00' * (512 - (16 * 4 + 2))
    return preamble + b''.join(paritition_data) + b'\x55\xaa'


def read_mbr(fobj):
    fobj.seek(0)
    data = fobj.read(512)
    if len(data) != 512:
        raise IOError('Unexpected EOF.')
    return data

    
def write_mbr(fobj, mbr_data):
    fobj.seek(0)
    fobj.write(mbr_data)
