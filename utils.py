# -*- coding: utf-8 -*-

from mips32 import Instruction, Data


def extract_data(in_file_path):
    inst_byte_size = 4
    PC = 64
    read_buf = b''
    is_break = False
    inst_mem = {}
    data_mem = {}
    inst_bin_list = []
    data_bin_list = []

    with open(in_file_path, 'r') as file_in:
        for read_buf in file_in.readlines():
            read_buf = read_buf.readlines()
            if not is_break:
                inst = Instruction(instruction_binary=read_buf, pc_val=PC)
                inst_mem[PC] = inst
                inst_bin_list.append(read_buf)
                is_break = inst.is_break()

            if is_break:
                data = Data(data_binary=read_buf, pc_val=PC)
                data_mem[PC] = data
                data_bin_list.append(read_buf)

            PC += inst_byte_size

    print(inst_mem)
    print(data_mem)
    print(inst_bin_list)
    print(data_bin_list)
    return inst_mem, data_mem, inst_bin_list, data_bin_list
