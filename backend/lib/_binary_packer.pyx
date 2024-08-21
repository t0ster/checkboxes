# cythonize -a -i lib/_binary_packer.pyx
cdef class BinaryPacker:
    @staticmethod
    def pack(int number, bint bit1):
        if number < 0 or number > 999999:
            raise ValueError("Number must be between 0 and 999999")

        cdef unsigned char[3] buffer
        buffer[0] = (number >> 12) & 0xFF
        buffer[1] = (number >> 4) & 0xFF
        buffer[2] = (number & 0x0F) << 4
        buffer[2] |= 0x01 if bit1 else 0
        # for some reason returns 8 bytes, need to slice
        # print(f"Debug:  len={len(buffer)}")
        return buffer[:3]

    @staticmethod
    def unpack(bytes buffer):
        if len(buffer) != 3:
            raise ValueError("Buffer must be exactly 3 bytes long")
        cdef int number = (buffer[0] << 12) | (buffer[1] << 4) | (buffer[2] >> 4)
        cdef bint bit1 = bool(buffer[2] & 0x01)
        return {"number": number, "bit1": bit1}
