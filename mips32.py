# -*- coding: utf-8 -*-

from enum import Enum, unique
from abc import abstractmethod


class Data:
    def __init__(self, data_str="0", endian='big', pc_val=148):
        self.data_str = data_str
        self.pc_val = pc_val
        self.int_val = signed_str_to_int(self.data_str)

    def __str__(self):
        return '{} {} {}'.format(self.data_str, str(self.pc_val), str(self.int_val))


class Instruction:
    """
    -----Category-1-----
    J, JR, BEQ, BGEZ, BGTZ, BLTZ
    BREAK
    SW, LW
    SLL, SRL, SRA
    NOP
    -----Category-2-----
    AND, NOR
    MUL
    SUB, ADD
    SLT
    """

    @unique
    class _Types(Enum):
        type_i = 1
        type_j = 2
        type_r = 3
        type_unknown = 4

        @classmethod
        def get_type(cls, opcode):
            _inst_dict = {'000010': cls.type_j,
                          '101011': cls.type_i, '100011': cls.type_i, '000100': cls.type_i, '000101': cls.type_i,
                          '000001': cls.type_i,
                          '000111': cls.type_i, '000110': cls.type_i, '001000': cls.type_i, '001001': cls.type_i,
                          '001010': cls.type_i,
                          '000000': cls.type_r}
            return _inst_dict[opcode]

    class _InstSet(Enum):
        # detail instructions for different types here, follow the format as the DummyInstruction below
        # INSTR_001000 = ('DummyInstruction', 'SW')

        def __init__(self, class_name, abbr):
            self.class_name = class_name
            self.abbr = abbr

        @property
        def get_instr_class(self):
            mod = __import__(__name__)
            return getattr(mod, self.class_name)

    def __init__(self, instr_str, endian='big', pc_val=600):
        self.instr_str = instr_str
        self.opcode = self.instr_str[0:6]
        self.type = Instruction._Types.get_type(opcode=self.opcode)
        self.pc_val = pc_val
        self.formatted_instr_bin_str = ''
        self.desc_str = ''
        self.dest = None
        self.op1_val = None
        self.op2_val = None

        self.formatted_instr_bin_str = self.instr_str[0:6] + ' ' + self.instr_str[6:11] + ' ' + self.instr_str[11:16] \
                                       + ' ' + self.instr_str[16:21] + ' ' + self.instr_str[21:26] + ' ' \
                                       + self.instr_str[26:32]
        # Dynamic binding the Instruction Type
        if self.type is Instruction._Types.type_j:
            self.__class__ = InstructionTypeJ
        elif self.type is Instruction._Types.type_i:
            self.__class__ = InstructionTypeI
        elif self.type is Instruction._Types.type_r:
            self.__class__ = InstructionTypeR

        self._parse_instr_binary()

    @abstractmethod
    def _parse_instr_binary(self):
        pass

    def __str__(self):
        return '{} {} {}'.format(self.formatted_instr_bin_str, str(self.pc_val), self.desc_str)

    def is_break(self):
        if self.__class__ is InstructionBreakpoint:
            return True
        else:
            return False
        
        

###############################################
# J Type Instructions
###############################################
class InstructionTypeJ(Instruction):
    """
    J type: |--6 opcode--|---26 target---|
    includes:
    J
    """

    # InstSet instr_code

    class _InstSet(Instruction._InstSet):
        INSTR_000010 = ('InstructionJump', 'J')

    def _parse_instr_binary(self):
        # print("J type Instruction")
        self.instr_code = InstructionTypeJ._InstSet['INSTR_' + self.opcode]
        self.__class__ = self.instr_code.get_instr_class
        self._inst_decode()

    @abstractmethod
    def _inst_decode(self):
        pass


class InstructionJump(InstructionTypeJ):
    """
    type J, p138: Jump. To branch within the current 256 MB-aligned region
    |--6J 000010--|---26 instr_index---|
    Format: J target
    Desc: This is a PC-region branch. The low 28 bits of the target address is the instr_index field shifted left 2 bits.
    The remaining upper bits are the corresponding bits of the address of the instruction in the delay
    slot (not the branch itself). Upper 4 bits of PC?
    """

    target_instr_index_str = ''

    def _inst_decode(self):
        self.dest = int(self.instr_str[6:32], 2) << 2

        # TODO: add the first 4 bits of the Jump, from PC?
        self.target_instr_index_str = str(int(self.instr_str[6:32], 2) << 2)
        self.desc_str = '{} #{}'.format(self.instr_code.abbr, self.target_instr_index_str)



###############################################
# I Type Instructions
###############################################
class InstructionTypeI(Instruction):
    """
    I type: |--6 opcode--|-5 rs-|-5 rt-|--16 target--|
    includes:
    SW, LW
    BEQ, BNE, BGEZ, BGTZ, BLEZ, BLTZ
    ADDI, ADDIU
    SLTI
    """

    # InstSet instr_code
    # register_s = ''
    # register_t = ''
    # offset = target = ''

    class _InstSet(Instruction._InstSet):
        INSTR_101011 = ('InstructionStoreWord', 'SW')
        INSTR_100011 = ('InstructionLoadWord', 'LW')
        INSTR_000100 = ('InstructionBranchOnEqual', 'BEQ')
        INSTR_000101 = ('InstructionBranchOnNotEqual', 'BNE')
        INSTR_000001_00001 = ('InstructionBranchOnGreaterThanOrEqualToZero', 'BGEZ')
        INSTR_000111 = ('InstructionBranchOnGreaterThanZero', 'BGTZ')
        INSTR_000110 = ('InstructionBranchOnLessThanOrEqualToZero', 'BLEZ')
        INSTR_000001_00000 = ('InstructionBranchOnLessThanZero', 'BLTZ')
        INSTR_001000 = ('InstructionAddImmediateWord', 'ADDI')
        INSTR_001001 = ('InstructionAddImmediateUnsignedWord', 'ADDIU')
        INSTR_001010 = ('InstructionSetOnLessThanImmediate', 'SLTI')

    def _parse_instr_binary(self):
        # print("I type Instruction")
        # offset variable is for convenience.
        self.register_s = self.instr_str[6:11]
        self.register_t = self.instr_str[11:16]
        self.offset = self.instr_str[16:32]
        self.target = self.offset

        if self.opcode == '000001':
            self.instr_code = InstructionTypeI._InstSet['INSTR_' + self.opcode + '_' + self.register_t]
        else:
            self.instr_code = InstructionTypeI._InstSet['INSTR_' + self.opcode]

        self.__class__ = self.instr_code.get_instr_class
        self._inst_decode()

    @abstractmethod
    def _inst_decode(self):
        pass




###############################################
# R Type Instructions
###############################################
class InstructionTypeR(Instruction):
    """
    R type: |--6 opcode--|-5 register s(rs)-|-5 register t(rt)-|--5 register d(rd)-|-5 shift(shamt)-|-6 function-|
    includes:
    BREAK, which is a special type, the middle 20 bytes are CODE
    SLT, SLTU
    SLL, SRL, SRA
    SUB, SUBU, ADD, ADDU
    AND, OR, XOR, NOR
    NOP
    """

    # InstSet instr_code
    # register_s = ''
    # register_t = ''
    # register_d = ''
    # shift_amount = ''
    # func_code = ''

    class _InstSet(Instruction._InstSet):
        INSTR_NOP = ('InstructionNoOperation', 'NOP')
        INSTR_SLL = ('InstructionShiftWordLeftLogical', 'SLL')
        INSTR_000010 = ('InstructionShiftWordRightLogical', 'SRL')
        INSTR_000011 = ('InstructionShiftWordRightArithmetic', 'SRA')
        INSTR_001101 = ('InstructionBreakpoint', 'BREAK')
        INSTR_100000 = ('InstructionAddWord', 'ADD')
        INSTR_100001 = ('InstructionAddUnsignedWord', 'ADDU')
        INSTR_100010 = ('InstructionSubtractWord', 'SUB')
        INSTR_100011 = ('InstructionSubtractUnsignedWord', 'SUBU')
        INSTR_100100 = ('InstructionAnd', 'AND')
        INSTR_100101 = ('InstructionOr', 'OR')
        INSTR_100110 = ('InstructionExclusiveOr', 'XOR')
        INSTR_100111 = ('InstructionNotOr', 'NOR')
        INSTR_101010 = ('InstructionSetOnLessThan', 'SLT')
        INSTR_101011 = ('InstructionSetOnLessThanUnsigned', 'SLTU')

    def _parse_instr_binary(self):
        # print("R type Instruction")
        # offset variable is for convenience.
        self.register_s = self.instr_str[6:11]
        self.register_t = self.instr_str[11:16]
        self.register_d = self.instr_str[16:21]
        self.shift_amount = self.instr_str[21:26]
        self.func_code = self.instr_str[26:32]

        if self.func_code == '000000':
            if self.register_s == '00000' and self.register_t == '00000' and self.register_d == '00000' and self.shift_amount == '00000':
                self.instr_code = InstructionTypeR._InstSet['INSTR_NOP']
            else:
                self.instr_code = InstructionTypeR._InstSet['INSTR_SLL']
        else:
            self.instr_code = InstructionTypeR._InstSet['INSTR_' + self.func_code]

        self.__class__ = self.instr_code.get_instr_class
        self._inst_decode()

    @abstractmethod
    def _inst_decode(self):
        pass


class InstructionBreakpoint(InstructionTypeR):
    """
    type R, (func_code)BREAK 001101, p84: Breakpoint: To cause a Breakpoint exception
    |--6 000000--|-20 CODE-|-6BREAK 001101-|
    Format: BREAK
    Desc: A breakpoint exception occurs, immediately and unconditionally transferring control to the exception handler.
    The code field is available for use as software parameters, but is retrieved by the exception handler only by
    loading the contents of the memory word containing the instruction.
    """

    def _inst_decode(self):
        self.code = self.register_s + self.register_t + self.register_d

        self.desc_str = '{}'.format(self.instr_code.abbr)
        
        

def signed_str_to_int(bin_str='0' * 32):
    """
    transfer the binary string to a signed integer value. Currently only support 16 bits binary strings.
      The string should be represented in two's complement format. Left most bits is the most significant bit.
    :param bin_str: binary strings to be converted
    :return: signed integer value
    """
    print(bin_str)
    print(bin_str[0] == '1')
    if bin_str[0] == '1':  # the string is negative number
        xor_operand = int('1' * len(bin_str), 2)  # get the xor operand based on the bit length of the binary
        return -((int(bin_str, 2) ^ xor_operand) + 1)
    elif bin_str[0] == '0':  # the string is a positive number
        return int(bin_str, 2)
    else:  
        raise RuntimeError('wrong binary string format')










