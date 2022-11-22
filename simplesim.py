# -*- coding: utf-8 -*-
from mips32 import Instruction, InstructionJump, InstructionJumpRegister, InstructionBranchOnEqual, InstructionBranchOnGreaterThanZero, InstructionBranchOnLessThanZero, InstructionStoreWord, InstructionLoadWord, InstructionShiftWordLeftLogical, InstructionShiftWordRightLogical, InstructionShiftWordRightArithmetic, InstructionAnd, InstructionNotOr, InstructionMulWord, InstructionSubtractWord, InstructionAddWord, InstructionSetOnLessThan, InstructionAddWord2, InstructionSubWord2, InstructionMulWord2, InstructionAnd2, InstructionSetOnLessThan2, signed_str_to_int
from utils import int_to_16bitstr

class SimpleSim:
    '''
    J, JR, BEQ, BGEZ, BLTZ
    BREAK
    SW, LW
    SLL, SRL, SRA
    NOP
    AND, NOR
    MUL
    SUB, ADD
    SLT
    '''

    def __init__(self, instr_mem, data_mem):
        self.RF = RegisterFile()
        self.DS = DataSegment(data_mem)
        self.instr_mem = instr_mem
        self.PC = 64
        self.cycle = 0
        self.is_over = False

    def next_instr(self):
        self.cycle += 1
        # print(self.cycle)
        cur_str = self.instr_mem[self.PC]
        if cur_str.is_break():
            self.is_over = True
            return

        # branch instructions
        if isinstance(cur_str, InstructionJump):
            self.PC = cur_str.dest
        elif isinstance(cur_str, InstructionJumpRegister):
            self.PC = self.RF.reg_read(int(cur_str.register_s, 2))
        else:
            self.PC += 4
            rg1 = self.RF.reg_read(int(cur_str.instr_str[6:11], 2))
            rg2 = self.RF.reg_read(int(cur_str.instr_str[11:16], 2))

        if isinstance(cur_str, InstructionBranchOnEqual):
            if self.RF.reg_read(cur_str.op1_val) == self.RF.reg_read(cur_str.op2_val):
                self.PC += cur_str.dest
        elif isinstance(cur_str, InstructionBranchOnGreaterThanZero):
            if self.RF.reg_read(int(cur_str.register_s, 2)) > 0:
                self.PC += signed_str_to_int(cur_str.offset + "00")
        elif isinstance(cur_str, InstructionBranchOnLessThanZero):
            if self.RF.reg_read(int(cur_str.register_s, 2)) < 0:
                self.PC += signed_str_to_int(cur_str.offset + "00")
        elif isinstance(cur_str, InstructionStoreWord):
            self.DS.mem_write(rg1 + cur_str.op1_val, rg2)
        elif isinstance(cur_str, InstructionLoadWord):
            self.RF.reg_write(
                cur_str.dest, self.DS.mem_read(cur_str.op1_val + rg1))
        elif isinstance(cur_str, InstructionShiftWordLeftLogical):
            self.RF.reg_write(cur_str.dest, signed_str_to_int(int_to_16bitstr(rg2)[cur_str.sa_val:] + "0"*cur_str.sa_val))
        elif isinstance(cur_str, InstructionShiftWordRightLogical):
            self.RF.reg_write(cur_str.dest, signed_str_to_int("0"*cur_str.sa_val + int_to_16bitstr(rg2)[:cur_str.sa_val]))
        elif isinstance(cur_str, InstructionShiftWordRightArithmetic):
            self.RF.reg_write(cur_str.dest, signed_str_to_int(int_to_16bitstr(rg2)[0]*cur_str.sa_val + int_to_16bitstr(rg2)[:cur_str.sa_val]))
        elif isinstance(cur_str, InstructionAnd):
            self.RF.reg_write(cur_str.dest, rg1 & rg2)
        elif isinstance(cur_str, InstructionNotOr):
            self.RF.reg_write(cur_str.dest, ~(rg1 | rg2))
        elif isinstance(cur_str, InstructionMulWord):  # not checked
            self.RF.reg_write(cur_str.dest, rg1 * rg2)
        elif isinstance(cur_str, InstructionSubtractWord):
            self.RF.reg_write(cur_str.dest, rg1 - rg2)
        elif isinstance(cur_str, InstructionAddWord):
            self.RF.reg_write(cur_str.dest, rg1 + rg2)
        elif isinstance(cur_str, InstructionSetOnLessThan):
            self.RF.reg_write(cur_str.dest, rg1 < rg2)
        elif isinstance(cur_str, InstructionAddWord2):
            self.RF.reg_write(cur_str.dest, rg1 + cur_str.imm_val)
        elif isinstance(cur_str, InstructionSubWord2):
            self.RF.reg_write(cur_str.dest, rg1 - cur_str.imm_val)
        elif isinstance(cur_str, InstructionMulWord2):
            self.RF.reg_write(cur_str.dest, rg1 * cur_str.imm_val)
        elif isinstance(cur_str, InstructionAnd2):
            self.RF.reg_write(cur_str.dest, rg1 & cur_str.imm_val)
        elif isinstance(cur_str, InstructionSetOnLessThan2):
            self.RF.reg_write(cur_str.dest, rg1 < cur_str.imm_val)


# m16 = lamda x : x 0xFFFF

class RegisterFile:
    """
    32 integer registers.
    """

    def __init__(self):
        self.size = 32
        self.print_width = 16
        self.R = [0] * self.size

    def __str__(self):
        desc_str = 'Registers'
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

    def __init__(self, data_mem):
        self._table = data_mem
        self.print_width = 8

    def __str__(self):
        desc_str = 'Data'
        cnt = 0
        for key, value in self._table.items():
            if cnt % self.print_width == 0:
                desc_str += '\n{}:'.format(key)
            desc_str += '\t{}'.format(value.int_val)
            cnt += 1

        return desc_str + '\n'

    def mem_write(self, mem_addr: int, value: int):
        self._table[mem_addr].int_val = value

    def mem_read(self, mem_addr: int) -> int:
        return self._table[mem_addr].int_val
