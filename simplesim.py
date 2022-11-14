# -*- coding: utf-8 -*-

class SimpleSim:
    def __init__(self, **data_mem):
        self.RF = RegisterFile()
        self.DS = DataSegment(**data_mem)


class RegisterFile:
    """
    32 integer registers.
    """

    def __init__(self):
        self.size = 32
        self.print_width = 16
        self.R = [0] * self.size

    def __str__(self):
        desc_str = 'Registers:'
        for idx in range(len(self.R)):
            if idx % self.print_width == 0:
                desc_str += '\nR{}:'.format(str(idx).zfill(2))
            desc_str += '\t' + str(self.R[idx])
        desc_str += '\n'
        return desc_str

    def reg_write(self, reg_addr: int, value: int):
        if reg_addr < 32 and reg_addr >= 0:
            self.R[reg_addr] = value
        else:
            raise Exception('Register address out of range!')

    def reg_read(self, reg_addr: int) -> int:
        if reg_addr < 32 and reg_addr >= 0:
            return self.R[reg_addr]
        else:
            raise Exception('Register address out of range!')


class DataSegment:
    """
    Data Segment of the memory. Starts from 64 of the program and until the end of the file.
    """

    def __init__(self, **data_mem):
        self._table = data_mem
        self.print_width = 8

    def __str__(self):
        desc_str = 'Data Segment:'
        cnt = 0
        for key, value in sorted(self._table.keys()):
            if cnt % self.print_width == 0:
                desc_str += '\n{}'.format(key)
            desc_str += '\t{}'.format(value)
            cnt += 1

        return desc_str + '\n'

    def mem_write(self, mem_addr: int, value: int):
        self._table[mem_addr] = value

    def mem_read(self, mem_addr: int) -> int:
        return self._table[mem_addr]
