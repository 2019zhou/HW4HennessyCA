# -*- coding: utf-8 -*-

from enum import Enum, unique
from abc import abstractmethod

class Data:
    def __init__(self, data_str="0", endian='big', pc_val=148):
        self.data_str = data_str
        self.pc_val = pc_val
        self.int_val = signed_str_to_int(self.data_str)

    def __str__(self):
        return '{}\t{}\t{}'.format(self.data_str, str(self.pc_val), str(self.int_val))


class Instruction:
    """
    -----Category-1-----
    J, JR, BEQ, BGEZ, BGTZ, BLTZ
    BREAK
    SW, LW
    SLL, SRL, SRA
    NOP
    AND, NOR
    MUL
    SUB, ADD
    SLT
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
        type_2 = 4
        type_unknown = 5

        @classmethod
        def get_type(cls, opcode):
            _inst_dict = {'000010': cls.type_j,
                          '101011': cls.type_i, '100011': cls.type_i, '000100': cls.type_i, '000101': cls.type_i, '000001': cls.type_i, '000111': cls.type_i, '000110': cls.type_i, '001000': cls.type_i, '001001': cls.type_i,
                          '001010': cls.type_i,
                          '000000': cls.type_r, '011100': cls.type_r,
                          '110000': cls.type_2, '110001': cls.type_2, '100001': cls.type_2, '110010': cls.type_2, '110011': cls.type_2,
                          '110101': cls.type_2}

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

    def __init__(self, instr_str, endian='big', pc_val=64):
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
        elif self.type is Instruction._Types.type_2:
            self.__class__ = InstructionType2

        self._parse_instr_binary()

    @abstractmethod
    def _parse_instr_binary(self):
        pass

    def __str__(self):
        return '{}\t{}\t{}'.format(self.formatted_instr_bin_str, str(self.pc_val), self.desc_str)

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
    The remaining upper bits are the corresponding bits of the address of the instruction in the delay slot (not the branch itself). 
    """

    target_instr_index_str = ''

    def _inst_decode(self):
        self.dest = int(self.instr_str[6:32], 2) << 2

        self.target_instr_index_str = str(int(self.instr_str[6:32], 2) << 2)
        self.desc_str = '{} #{}'.format(
            self.instr_code.abbr, self.target_instr_index_str)


###############################################
# I Type Instructions
###############################################
class InstructionTypeI(Instruction):
    """
    I type: |--6 opcode--|-5 rs-|-5 rt-|--16 target--|
    includes:
    SW, LW
    BEQ, BGTZ, BLTZ
    """

    # InstSet instr_code
    # register_s = ''
    # register_t = ''
    # offset = target = ''

    class _InstSet(Instruction._InstSet):
        INSTR_101011 = ('InstructionStoreWord', 'SW')
        INSTR_100011 = ('InstructionLoadWord', 'LW')
        INSTR_000100 = ('InstructionBranchOnEqual', 'BEQ')
        INSTR_000111 = ('InstructionBranchOnGreaterThanZero', 'BGTZ')
        INSTR_000001_00000 = ('InstructionBranchOnLessThanZero', 'BLTZ')

    def _parse_instr_binary(self):
        # print("I type Instruction")
        # offset variable is for convenience.
        self.register_s = self.instr_str[6:11]
        self.register_t = self.instr_str[11:16]
        self.offset = self.instr_str[16:32]
        self.target = self.offset
        
        self.op1_val = int(self.register_s, 2)
        self.op2_val = int(self.register_t, 2)

        if self.opcode == '000001':
            self.instr_code = InstructionTypeI._InstSet['INSTR_' +
                                                        self.opcode + '_' + self.register_t]
        else:
            self.instr_code = InstructionTypeI._InstSet['INSTR_' + self.opcode]

        self.__class__ = self.instr_code.get_instr_class
        self._inst_decode()

    @abstractmethod
    def _inst_decode(self):
        pass


class InstructionLoadWord(InstructionTypeI):
    """
    type I, SW 100011, p161: Load Word: To load a word from memory as a signed value
    |--6SW 100011--|-5 base-|-5 rt-|--16 offset--|
    Format: LW rt, offset(base)
    Desc: rt ← memory[base+offset]
    The contents of the 32-bit word at the memory location specified by the aligned effective address are fetched,
    sign-extended to the GPR register length if necessary, and placed in GPR rt. The 16-bit signed offset is added
    to the contents of GPR base to form the effective address.
    """

    def _inst_decode(self):
        self.base = self.register_s
        self.dest = int(self.register_t, 2)
        self.op1_val = int(self.offset, 2)
        self.op2_val = int(self.base, 2)

        self.desc_str = '{} R{}, {}(R{})'.format(self.instr_code.abbr, int(self.register_t, 2), int(self.offset, 2),
                                                 int(self.base, 2))


class InstructionStoreWord(InstructionTypeI):
    """
    type I, SW 101011, p270: Store Word: To store a word to memory
    |--6SW 101011--|-5 base-|-5 rt-|--16 offset--|
    Format: SW rt, offset(base)
    Desc: memory[base+offset] ← rt
    The least-significant 32-bit word of register rt is stored in memory at the location specified by the aligned
    effective address. The 16-bit signed offset is added to the contents of GPR base to form the effective address.
    """

    def _inst_decode(self):
        self.base = self.register_s
        self.dest = int(self.register_t, 2)  # data to be stored
        self.op1_val = int(self.offset, 2)  # base, which is a const
        self.op2_val = int(self.base, 2)  # dest offset from reg

        self.desc_str = '{} R{}, {}(R{})'.format(self.instr_code.abbr, int(self.register_t, 2), int(self.offset, 2),
                                                 int(self.base, 2))


class InstructionBranchOnEqual(InstructionTypeI):
    """
    type I, BEQ 000100, p60: Branch on Equal: To compare GPRs then do a PC-relative conditional branch
    |--6SW 000100--|-5 rs-|-5 rt-|--16 offset--|
    Format: BEQ rs, rt, offset
    Desc: if rs = rt then branch
    An 18-bit signed offset (the 16-bit offset field shifted left 2 bits) is added to the address of the instruction
    following the branch (not the branch itself), in the branch delay slot, to form a PC-relative effective target
    address. If the contents of GPR rs and GPR rt are equal, branch to the effective target address after the
    instruction in the delay slot is executed.
    P.S. Left Shift 2 bits
    """

    def _inst_decode(self):
        self.op1_val = int(self.register_s, 2)
        self.op2_val = int(self.register_t, 2)
        self.dest = signed_str_to_int(self.offset) << 2

        self.desc_str = '{} R{}, R{}, #{}'.format(self.instr_code.abbr, int(self.register_s, 2),
                                                  int(self.register_t, 2), signed_str_to_int(self.offset) << 2)


class InstructionBranchOnGreaterThanZero(InstructionTypeI):
    """
    type I, BGTZ 000111, p69: Branch on Greater Than Zero: To test a GPR then do a PC-relative conditional branch
    |--6BGTZ 000111--|-5 rs-|-5 00000-|--16 offset--|
    Format: BGTZ rs, offset
    Desc: if rs > 0 then branch
    An 18-bit signed offset (the 16-bit offset field shifted left 2 bits) is added to the address of the instruction
    following the branch (not the branch itself), in the branch delay slot, to form a PC-relative effective target
    address. If the contents of GPR rs are greater than zero (sign bit is 0 but value not zero), branch to the
    effective target address after the instruction in the delay slot is executed.
    P.S. Left Shift 2 bits
    """

    def _inst_decode(self):
        self.desc_str = '{} R{}, #{}'.format(self.instr_code.abbr, int(self.register_s, 2),
                                             signed_str_to_int(self.offset) << 2)


class InstructionBranchOnLessThanZero(InstructionTypeI):
    """
    type I, BLTZ 000001, p75: Branch on Less Than Zero: To test a GPR then do a PC-relative conditional branch
    |--6REGIMM 000001--|-5 rs-|-5BLTZ 00000-|--16 offset--|
    Format: BLTZ rs, offset
    Desc: if rs < 0 then branch
    An 18-bit signed offset (the 16-bit offset field shifted left 2 bits) is added to the address of the instruction
    following the branch (not the branch itself), in the branch delay slot, to form a PC-relative effective target
    address. If the contents of GPR rs are less than zero (sign bit is 1), branch to the effective target address after
    the instruction in the delay slot is executed.
    P.S. !!!!!! same opcode as BGEZ. Left Shift 2 bits
    """

    def _inst_decode(self):
        self.desc_str = '{} R{}, #{}'.format(self.instr_code.abbr, int(self.register_s, 2),
                                             signed_str_to_int(self.offset) << 2)


###############################################
# R Type Instructions
###############################################
class InstructionTypeR(Instruction):
    """
    R type: |--6 opcode--|-5 register s(rs)-|-5 register t(rt)-|--5 register d(rd)-|-5 shift(shamt)-|-6 function-|
    includes:
    BREAK, which is a special type, the middle 20 bytes are CODE
    ADD, SUB  // category 1
    AND, NOR  // category 1
    SLL, SRL, SRA
    JR
    SLT  // category 1
    MUL  // category 1
    NOP
    """

    # InstSet instr_code
    # register_s = ''
    # register_t = ''
    # register_d = ''
    # shift_amount = ''
    # func_code = ''

    class _InstSet(Instruction._InstSet):
        INSTR_100000 = ('InstructionAddWord', 'ADD')
        INSTR_100010 = ('InstructionSubtractWord', 'SUB')
        INSTR_100100 = ('InstructionAnd', 'AND')
        INSTR_100111 = ('InstructionNotOr', 'NOR')
        INSTR_SLL = ('InstructionShiftWordLeftLogical', 'SLL')
        INSTR_000010 = ('InstructionShiftWordRightLogical', 'SRL')
        INSTR_000011 = ('InstructionShiftWordRightArithmetic', 'SRA')
        INSTR_101010 = ('InstructionSetOnLessThan', 'SLT')
        INSTR_MUL = ('InstructionMulWord', 'MUL')
        INSTR_NOP = ('InstructionNoOperation', 'NOP')
        INSTR_001101 = ('InstructionBreakpoint', 'BREAK')
        INSTR_001000 = ('InstructionJumpRegister', 'JR')

    def _parse_instr_binary(self):
        # print("R type Instruction")
        # offset variable is for convenience.
        self.register_s = self.instr_str[6:11]
        self.register_t = self.instr_str[11:16]
        self.register_d = self.instr_str[16:21]
        self.shift_amount = self.instr_str[21:26]
        self.func_code = self.instr_str[26:32]

        self.dest = int(self.register_d, 2)
        self.op1_val = int(self.register_s, 2)
        self.op2_val = int(self.register_t, 2)
        self.sa_val = int(self.shift_amount, 2)

        if self.func_code == '000000':
            if self.register_s == '00000' and self.register_t == '00000' and self.register_d == '00000' and self.shift_amount == '00000':
                self.instr_code = InstructionTypeR._InstSet['INSTR_NOP']
            else:
                self.instr_code = InstructionTypeR._InstSet['INSTR_SLL']
        elif self.func_code == '000010' and self.opcode == '011100':
            self.instr_code = InstructionTypeR._InstSet['INSTR_MUL']
        else:
            self.instr_code = InstructionTypeR._InstSet['INSTR_' + self.func_code]

        self.__class__ = self.instr_code.get_instr_class
        self._inst_decode()

    @abstractmethod
    def _inst_decode(self):
        pass


class InstructionAddWord(InstructionTypeR):
    """
    type R, (func_code)ADD 100000, p34, Add Word: To add 32-bit integers. If an overflow occurs, then trap.
    |--6 000000--|-5 rs-|-5 rt-|--5 rd-|-5 00000-|-6ADD 100000-|
    Format: ADD rd, rs, rt
    Desc: rd ← rs + rt
    The 32-bit word value in GPR rt is added to the 32-bit value in GPR rs to produce a 32-bit result.
    • If the addition results in 32-bit 2’s complement arithmetic overflow, the destination register is not modified
    and an Integer Overflow exception occurs.
    • If the addition does not overflow, the 32-bit result is placed into GPR rd.
    """

    def _inst_decode(self):
        self.desc_str = '{} R{}, R{}, R{}'.format(self.instr_code.abbr, int(self.register_d, 2),
                                                  int(self.register_s, 2), int(self.register_t, 2))


class InstructionSubtractWord(InstructionTypeR):
    """
    type R, (func_code)SUB 100010, p266, Subtract Word: To subtract 32-bit integers. If overflow occurs, then trap
    |--6 000000--|-5 rs-|-5 rt-|--5 rd-|-5 00000-|-6SUB 100010-|
    Format: SUB rd, rs, rt
    Desc: rd ← rs - rt
    The 32-bit word value in GPR rt is subtracted from the 32-bit value in GPR rs to produce a 32-bit result. If the
    subtraction results in 32-bit 2’s complement arithmetic overflow, then the destination register is not modified and
    an Integer Overflow exception occurs. If it does not overflow, the 32-bit result is placed into GPR rd.
    P.S. signed, overflow
    """

    def _inst_decode(self):
        self.desc_str = '{} R{}, R{}, R{}'.format(self.instr_code.abbr, int(self.register_d, 2),
                                                  int(self.register_s, 2), int(self.register_t, 2))


class InstructionAnd(InstructionTypeR):
    """
    type R, (func_code)ADD 100100, p42, And: To do a bitwise logical AND
    |--6 000000--|-5 rs-|-5 rt-|--5 rd-|-5 00000-|-6AND 100100-|
    Format: AND rd, rs, rt
    Desc: rd ← rs AND rt
    The contents of GPR rs are combined with the contents of GPR rt in a BITWISE logical AND operation. The result is
    placed into GPR rd.
    """

    def _inst_decode(self):
        self.desc_str = '{} R{}, R{}, R{}'.format(self.instr_code.abbr, int(self.register_d, 2),
                                                  int(self.register_s, 2), int(self.register_t, 2))


class InstructionNotOr(InstructionTypeR):
    """
    type R, (func_code)XOR 100111, p217 Not Or: To do a bitwise logical NOT OR
    |--6 000000--|-5 rs-|-5 rt-|--5 rd-|-5 00000-|-6OR 100111-|
    Format: NOR rd, rs, rt
    Desc:  rd ← rs NOR rt
    The contents of GPR rs are combined with the contents of GPR rt in a bitwise logical NOR operation. The result is
    placed into GPR rd.
    """

    def _inst_decode(self):
        self.desc_str = '{} R{}, R{}, R{}'.format(self.instr_code.abbr, int(self.register_d, 2),
                                                  int(self.register_s, 2), int(self.register_t, 2))


class InstructionShiftWordLeftLogical(InstructionTypeR):
    """
    type R, (func_code)SLL 000000(Same as NOP), p254, Shift Word Left Logical: To left-shift a word by a fixed
    number of bits
    |--6 000000--|-5 00000-|-5 rt-|--5 rd-|-5 sa-|-6SLL 000000-|
    Format: SLL rd, rt, sa
    Desc: rd ← rt << sa
    The contents of the low-order 32-bit word of GPR rt are shifted left, inserting zeros into the emptied bits;
    the word result is placed in GPR rd. The bit-shift amount is specified by sa.
    P.S. Same func_code as NOP
    """

    def _inst_decode(self):
        self.desc_str = '{} R{}, R{}, #{}'.format(self.instr_code.abbr, int(self.register_d, 2),
                                                  int(self.register_t, 2), int(self.shift_amount, 2))


class InstructionShiftWordRightLogical(InstructionTypeR):
    """
    type R, (func_code)SRL 000010, p263, Shift Word Right Logical: To execute a logical right-shift of a word by a
    fixed number of bits
    |--6 000000--|-5SHIFT 00000-|-5 rt-|--5 rd-|-5 sa-|-6SRL 000010-|
    Format: SRL rd, rt, sa
    Desc: rd ← rt << sa
    The contents of the low-order 32-bit word of GPR rt are shifted right, inserting zeros into the emptied bits;
    the word result is placed in GPR rd. The bit-shift amount is specified by sa.
    """

    def _inst_decode(self):
        self.desc_str = '{} R{}, R{}, #{}'.format(self.instr_code.abbr, int(self.register_d, 2),
                                                  int(self.register_t, 2), int(self.shift_amount, 2))


class InstructionShiftWordRightArithmetic(InstructionTypeR):
    """
    type R, (func_code)SRA 000011, p261, Shift Word Right Arithmetic: To execute an arithmetic right-shift of a word by
    a fixed number of bits
    |--6 000000--|-5 00000-|-5 rt-|--5 rd-|-5 sa-|-6SRA 000011-|
    Format: SRA rd, rt, sa
    Desc: rd ← rt >> sa (arithmetic)
    The contents of the low-order 32-bit word of GPR rt are shifted right, duplicating the sign-bit (bit 31) in the
    emptied bits; the word result is placed in GPR rd. The bit-shift amount is specified by sa.
    """

    def _inst_decode(self):
        self.desc_str = '{} R{}, R{}, #{}'.format(self.instr_code.abbr, int(self.register_d, 2),
                                                  int(self.register_t, 2), int(self.shift_amount, 2))


class InstructionJumpRegister(InstructionTypeR):
    """
    type R, (func_code)JR 001000, p145: To execute a branch to an instruction address in a register
    |--6 000000--|-5 rs-|-10 00000-00000-|-5 00000-|-6JR 001000-|
    Format: JR rs
    Desc: PC ← rs
    Jump to the effective target address in GPR rs. Execute the instruction following the jump, in the branch delay slot, before jumping.
    For processors that implement the MIPS16e ASE, set the ISA Mode bit to the value in GPR rs bit 0. Bit 0 of the target address is always zero so that no Address Exceptions occur when bit 0 of the source register is one
    """

    def _inst_decode(self):
        self.desc_str = '{} R{}'.format(
            self.instr_code.abbr, int(self.register_s, 2))


class InstructionMulWord(InstructionTypeR):
    """
    type R, (func_code)MUL 000010, p207, Multiply Word to GPR: To multiply two words and write the result to a GPR.
    |--6 011100--|-5 rs-|-5 rt-|--5 rd-|-5 00000-|-6MUL 000010-|
    Format: MUL rd, rs, rt
    Desc: rd ← rs * rt
    The 32-bit word value in GPR rs is multiplied by the 32-bit value in GPR rt, treating both operands as signed values, 
    to produce a 64-bit result. The least significant 32 bits of the product are written to GPR rd. The contents of HI and
    LO are UNPREDICTABLE after the operation. No arithmetic exception occurs under any circumstances.
    """

    def _inst_decode(self):
        self.desc_str = '{} R{}, R{}, R{}'.format(self.instr_code.abbr, int(self.register_d, 2),
                                                  int(self.register_s, 2), int(self.register_t, 2))


class InstructionSetOnLessThan(InstructionTypeR):
    """
    type R, (func_code)SLT 101010, p256: Set on Less Than: To record the result of a less-than comparison
    |--6 000000--|-5 rs-|-5 rt-|--5 rd-|-5 00000-|-6SLT 101010-|
    Format: SLT rd, rs, rt
    Desc: rd ← (rs < rt)
    Compare the contents of GPR rs and GPR rt as signed integers and record the Boolean result of the comparison in
    GPR rd. If GPR rs is less than GPR rt, the result is 1 (true); otherwise, it is 0 (false). The arithmetic
    comparison does not cause an Integer Overflow exception.
    P.S. rs and rd are SIGNED integers
    """

    def _inst_decode(self):
        self.desc_str = '{} R{}, R{}, R{}'.format(self.instr_code.abbr, int(self.register_d, 2),
                                                  int(self.register_s, 2), int(self.register_t, 2))


class InstructionNoOperation(InstructionTypeR):
    """
    type R, (func_code)NOP 000000(Same as SLL), p254, No operation: To perform no operation.
    number of bits
    |--6 000000--|-5 00000-|-5 rt-|--5 rd-|-5 sa-|-6SLL 000000-|
    Format: NOP
    Desc:
    NOP is the assembly idiom used to denote no operation. The actual instruction is interpreted by the hardware as
    SLL r0, r0, 0.
    """

    def _inst_decode(self):
        self.desc_str = '{}'.format(self.instr_code.abbr)


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


###############################################
# Category 2 Instructions
###############################################
class InstructionType2(Instruction):
    """100100
    Category 2 type: |-1 Imm|--5 opcode--|-5 register s(rs)-|-5 register t(rt)-|--16 immediate-|
    includes:
    ADD, SUB  // category 2
    AND, NOR  // category 2
    SLT  // category 2
    MUL  // category 2
    """

    # InstSet instr_code
    # register_s = ''
    # register_t = ''
    # immediate = ''

    class _InstSet(Instruction._InstSet):
        INSTR_110000 = ('InstructionAddWord2', 'ADD')
        INSTR_110001 = ('InstructionSubWord2', 'SUB')
        INSTR_100001 = ('InstructionMulWord2', 'MUL')
        INSTR_110010 = ('InstructionAnd2', 'AND')
        INSTR_110011 = ('InstructionNotOr2', 'NOR')
        INSTR_110101 = ('InstructionSetOnLessThan2', 'SLT')

    def _parse_instr_binary(self):
        # print("Category 2 type Instruction")
        # offset variable is for convenience.
        self.register_s = self.instr_str[6:11]
        self.register_t = self.instr_str[11:16]
        self.immediate = self.instr_str[16:32]

        self.op1_val = int(self.register_s, 2)
        self.dest = int(self.register_t, 2)
        self.imm_val = int(self.immediate, 2)

        self.instr_code = InstructionType2._InstSet['INSTR_' + self.opcode]
        self.__class__ = self.instr_code.get_instr_class
        self._inst_decode()

    @abstractmethod
    def _inst_decode(self):
        pass


class InstructionAddWord2(InstructionType2):
    """
    type 2, (func_code)ADD 10000 :
    |-1 Imm|--5 opcode--|-5 register s(rs)-|-5 register t(rt)-|--16 immediate-|
    Format: ADD rt, rs, immediate
    Desc: rt ← rs + immediate
    """

    def _inst_decode(self):
        self.desc_str = '{} R{}, R{}, #{}'.format(self.instr_code.abbr, int(self.register_t, 2),
                                                  int(self.register_s, 2), signed_str_to_int(self.immediate))


class InstructionSubWord2(InstructionType2):
    """
    type 2, (func_code)Sub 10001 :
    |-1 Imm|--5 opcode--|-5 register s(rs)-|-5 register t(rt)-|--16 immediate-|
    Format: SUB rt, rs, immediate
    Desc: rt ← rs - immediate
    """

    def _inst_decode(self):
        self.desc_str = '{} R{}, R{}, #{}'.format(self.instr_code.abbr, int(self.register_t, 2),
                                                  int(self.register_s, 2), signed_str_to_int(self.immediate))


class InstructionMulWord2(InstructionType2):
    """
    type 2, (func_code)Sub 00001 :
    |-1 Imm|--5 opcode--|-5 register s(rs)-|-5 register t(rt)-|--16 immediate-|
    Format: MUL rt, rs, immediate
    Desc: rt ← rs * immediate
    """

    def _inst_decode(self):
        self.desc_str = '{} R{}, R{}, #{}'.format(self.instr_code.abbr, int(self.register_t, 2),
                                                  int(self.register_s, 2), signed_str_to_int(self.immediate))


class InstructionAnd2(InstructionType2):
    """
    type 2, (func_code) NOR 10011 :
    |-1 Imm|--5 opcode--|-5 register s(rs)-|-5 register t(rt)-|--16 immediate-|
    Format: And rt, rs, immediate
    Desc: rt ← rs & immediate
    """

    def _inst_decode(self):
        self.desc_str = '{} R{}, R{}, #{}'.format(self.instr_code.abbr, int(self.register_t, 2),
                                                  int(self.register_s, 2), signed_str_to_int(self.immediate))


class InstructionSetOnLessThan2(InstructionType2):
    """
    type 2, (func_code)SLT 10101:
    |-1 Imm|--5 opcode--|-5 register s(rs)-|-5 register t(rt)-|--16 immediate-|
    Format: SLT rt, rs, immediate
    Desc: rt ← (rs < immediate)
    """

    def _inst_decode(self):
        self.desc_str = '{} R{}, R{}, #{}'.format(self.instr_code.abbr, int(self.register_t, 2),
                                                  int(self.register_s, 2), signed_str_to_int(self.immediate))


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
