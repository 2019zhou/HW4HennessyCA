# -*- coding: utf-8 -*-

from mips32 import Instruction, Data
from collections import OrderedDict

def extract_data(in_file_path):
    inst_byte_size = 4
    PC = 64
    read_buf = b''
    is_break = False
    inst_mem = OrderedDict()
    data_mem = OrderedDict()

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


def int_to_16bitstr(val):
    """
    transfer the signed integer value to str. Currently only support 16 bits binary strings.
      The string should be represented in two's complement format. Left most bits is the most significant bit.
    :param bin_str: binary strings to be converted
    :return: two's complement format string
    """
    if val < 0:
        return format(val & 0xFFFFFFFF, 'b').zfill(32)
    else:
        return format(val, 'b').zfill(32)


def signed_str_to_int(bin_str='0' * 32):
    """
    transfer the binary string to a signed integer value. Currently only support 16 bits binary strings.
      The string should be represented in two's complement format. Left most bits is the most significant bit.
    :param bin_str: binary strings to be converted
    :return: signed integer value
    """
    if bin_str[0] == '1':  # the string is negative number
        # get the xor operand based on the bit length of the binary
        xor_operand = int('1' * len(bin_str), 2)
        return -((int(bin_str, 2) ^ xor_operand) + 1)
    elif bin_str[0] == '0':  # the string is a positive number
        return int(bin_str, 2)
    else:
        raise RuntimeError('wrong binary string format')