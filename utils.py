# -*- coding: utf-8 -*-

from mips32 import Instruction, Data
import collections

def extract_data(in_file_path):
    inst_byte_size = 4
    PC = 64
    read_buf = b''
    is_break = False
    inst_mem = collections.OrderedDict()
    data_mem = collections.OrderedDict()

    with open(in_file_path, 'r') as file_in:
        for read_buf in file_in.readlines():
            read_buf = read_buf.strip()
            if not is_break:
                inst = Instruction(instr_str=read_buf, pc_val=PC)
                inst_mem[PC] = inst
                is_break = inst.is_break()
            else:
                data = Data(data_str=read_buf, pc_val=PC)
                data_mem[PC] = data

            PC += inst_byte_size

    # print(inst_mem)
    # print(data_mem)
    # print(inst_bin_list)
    # print(data_bin_list)
    return inst_mem, data_mem
