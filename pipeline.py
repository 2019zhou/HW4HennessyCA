from mips32 import Instruction, InstructionJump, InstructionJumpRegister, InstructionBranchOnEqual, InstructionBranchOnGreaterThanZero, InstructionBranchOnLessThanZero, InstructionStoreWord, InstructionLoadWord, InstructionShiftWordLeftLogical, InstructionShiftWordRightLogical, InstructionShiftWordRightArithmetic, InstructionAnd, InstructionNotOr, InstructionMulWord, InstructionSubtractWord, InstructionAddWord, InstructionSetOnLessThan, InstructionAddWord2, InstructionSubWord2, InstructionMulWord2, InstructionAnd2, InstructionSetOnLessThan2, InstructionNoOperation, InstructionBreakpoint, signed_str_to_int
from collections import OrderedDict
from enum import Enum

from utils import int_to_16bitstr


class _InstTypes(Enum):
    SL = 1
    ALU = 2
    ALUB = 3
    BRCH = 4
    UKNW = 5


class _PipelineInstEntry:
    def __init__(self, inst: Instruction):
        """
        NOP, Branch, BREAK: only IF;
        SW: IF, Issue, MEM;
        LW: IF, Issue, MEM, WB;
        SLL, SRL ,SRA and MUL: IF, Issue, ALUB, WB
        Other instructions: IF, Issue, ALU, WB.

        maintain the instruction status table 

        """
        self.inst = inst
        self.pc_val = inst.pc_val
        self.exec_cycle = 0
        self.dest = inst.dest
        self.result = None

        # self.fetch_cycle = -1
        # self.issue_cycle = -1
        # self.wb_cycle = -1
        # self.is_issued = False
        # self.is_wbed = False
        # self.is_execed = False

    def get_type(self) -> _InstTypes:
        branch_inst_set = (InstructionJump, InstructionJumpRegister,
                           InstructionBranchOnEqual,
                           InstructionBranchOnGreaterThanZero,
                           InstructionBranchOnLessThanZero)
        sl_inst_set = (InstructionStoreWord, InstructionLoadWord)
        alu_inst_set = (InstructionShiftWordLeftLogical, InstructionShiftWordRightLogical,
                        InstructionShiftWordRightArithmetic, InstructionMulWord, InstructionAddWord2, InstructionSubWord2, InstructionAnd2, InstructionSetOnLessThan2)
        alub_inst_set = (InstructionAnd, InstructionNotOr, InstructionMulWord,
                         InstructionSubtractWord, InstructionAddWord, InstructionSetOnLessThan, InstructionMulWord2)

        # to do add support for category 2 instructions

        if isinstance(self.inst, alu_inst_set):
            inst_type = _InstTypes.ALU
        elif isinstance(self.inst, alub_inst_set):
            inst_type = _InstTypes.ALUB
        elif isinstance(self.inst, sl_inst_set):
            inst_type = _InstTypes.SL
        elif isinstance(self.inst, branch_inst_set):
            inst_type = _InstTypes.BRCH
        else:
            inst_type = _InstTypes.UKNW
        return inst_type


# maintain the register result status table
# There are only two function unit namely alu and alub
# thus, register is either allocated in alu or alub
class _RegisterAllocationUnit:
    def __init__(self):
        self.inalu = False
        self.inalub = False

    def reset(self):
        self.inalu = False
        self.inalub = False


class Pipeline:
    pc = 64
    cycle = 0
    inst_size = 4

    def __init__(self, inst_mem, data_mem):
        # 0 for executed instruction, 1 for waiting instruction
        self.IFUnit = [""]*2
        self.PreIssue = Buffer("Pre-Issue", 4)
        self.PreALU = Queue("Pre-ALU", 2)
        self.PreALUB = Queue("Pre-ALUB", 2)
        self.PreMEM = Queue("Pre-MEM", 2)
        self.PostMEM = Buffer("Post-MEM", 1)
        self.PostALU = Buffer("Post-ALU", 1)
        self.PostALUB = Buffer("Post-ALUB", 1)

        self.inst_mem = inst_mem
        self.RF = RegisterFile()
        self.DS = DataSegment(data_mem)

        self.FU = FunctionalUnitStatus(self.RF)

        self.next_pc = self.pc
        self.is_over = False

    def next_cycle(self):
        self.cycle += 1

        if self.is_over:
            return

        # fetch and decode
        self.fetch()
        # issue
        self.issue()
        # alu
        self.alu()
        # alub
        self.alub()
        # mem
        self.mem()
        # wb
        self.wb()

        # all the buffer and the queue updated
        # to simulation the parallism
        self.PreIssue.update()
        self.PreALU.update()
        self.PostALU.update()
        self.PreALUB.update()
        self.PostALUB.update()
        self.PreMEM.update()
        self.PostMEM.update()
        self.pc = self.next_pc

    def snapshotifunit(self):
        desc_str = 'IF Unit:\n\tWaiting Instruction: {}\n'.format(
            self.IFUnit[1])
        desc_str += "\tExecuted Instruction: {}\n".format(self.IFUnit[0])
        return desc_str

    def fetch(self):
        """
        Instruction Fetch unit can fetch and decode at most two instructions at each cycle (in program order). The unit should check all the following conditions before it can fetch further instructions.
        1. If the fetch unit is stalled at the end of previous cycle, no instruction can be fetched at the current cycle. The fetch unit can be stalled due to a branch instruction
        2. If there is no empty slot in the Pre-issue buffer at the end of the previous cycle, no instruction can be fetched at the current cycle.
        3. If there is only one empty slot in the Pre-issue buffer at the end of the previous cycle, only one instruction can be fetched at the current cycle.
        """
        FetchNum = 0
        MaxIssueNum = 2
        while True:
            # 1. decode at most two instructions at each cycle
            if FetchNum >= MaxIssueNum:
                break
            # 2. check if there is no empty slot in the Pre-issue buffer
            if self.PreIssue.sync_isfull():
                break
            # fetch instruction
            next_inst_to_fetch = self.inst_mem.get(self.pc, None)
            pinst = _PipelineInstEntry(next_inst_to_fetch)
            self.next_pc = self.pc + 4
            # decode instruction and put it into Pre-Issue buffer
            if pinst.get_type() in (_InstTypes.ALU, _InstTypes.SL, _InstTypes.ALUB) or isinstance(next_inst_to_fetch, InstructionNoOperation):
                self.PreIssue.add_entry(pinst)
                FetchNum += 1
            elif pinst.get_type() == _InstTypes.BRCH:
                inst = next_inst_to_fetch
                if isinstance(inst, InstructionJump):
                    self.next_pc = inst.dest
                # check whether the register are ready
                Ready = False
                if isinstance(inst, InstructionJumpRegister):
                    if self.RF.is_ready(inst.op1_val):
                        self.next_pc = self.RF.reg_read(inst.op1_val)
                        Ready = True
                elif isinstance(inst, InstructionBranchOnEqual):
                    if self.RF.is_ready(inst.op1_val) and self.RF.is_ready(inst.op2_val):
                        if self.RF.reg_read(inst.op1_val) == self.RF.reg_read(inst.op2_val):
                            self.next_pc = self.pc + inst.dest + 4
                        Ready = True
                elif isinstance(inst, InstructionBranchOnGreaterThanZero):
                    if self.RF.is_ready(inst.op1_val):
                        if self.RF.reg_read(inst.op1_val) > 0:
                            self.next_pc = self.pc + \
                                signed_str_to_int(inst.offset + "00") + 4
                        Ready = True
                elif isinstance(inst, InstructionBranchOnLessThanZero):
                    if self.RF.is_ready(inst.op1_val):
                        if self.RF.reg_read(inst.op1_val) > 0:
                            self.next_pc = self.pc + \
                                signed_str_to_int(inst.offset + "00") + 4
                        Ready = True
                # means it has been executed
                if Ready:
                    self.IFUnit[0] = str(inst.desc_str)
                else:
                    self.IFUnit[1] = str(inst.desc_str)
                break
            elif isinstance(next_inst_to_fetch, InstructionBreakpoint):
                self.is_over = True
                break
        return

    def issue(self):
        """
        Issue unit follows the basic Scoreboard algorithm to issue instructions. It can issue at most two instruction out-of-order per cycle. When an instruction is issued, it is removed from the Pre-issue Buffer before the end of current cycle. The issue unit searches from entry 0 to entry 3 (in that order) of Pre-issue buffer and issues instructions if:
        - No structural hazards (the corresponding queue, e.g., Pre-ALU has empty slots at the end of the previous cycle)
        - No WAW hazards with active instructions (issued but not finished, or earlier not-issued instructions)
        - No WAR hazards with earlier not-issued instructions
        - For MEM instructions, all the source registers are ready at the end of the previous cycle
        - The load instruction must wait until all the previous stores are issued
        - The stores must be issued in order
        """
        IssueNum = 0
        MaxIssueNum = 2
        sz = self.PreIssue.size()

        LWSeq = True

        for idx in range(sz):
            if IssueNum >= MaxIssueNum:
                break
            pinst = self.PreIssue.get(idx)
            if pinst.get_type() == _InstTypes.ALUB:
                if self.PreALUB.isfull():
                    continue
                elif self.FU.add_entry(pinst):
                    IssueNum += 1
                    self.PreALUB.add_entry(pinst)
                    self.PreIssue.pop_entry(idx)
            elif pinst.get_type() == _InstTypes.ALU:
                if self.PreALU.isfull():
                    continue
                elif self.FU.add_entry(pinst):
                    IssueNum += 1
                    self.PreALU.add_entry(pinst)
                    self.PreIssue.pop_entry(idx)
            elif pinst.get_type() == _InstTypes.SL:
                inst = pinst.inst
                if LWSeq:
                    if self.PreMEM.isfull():
                        if not isinstance(pinst.inst, InstructionLoadWord):
                            LWSeq = False
                        continue
                    if self.RF.is_ready(inst.dest) and self.RF.is_ready(inst.op2_val):
                        IssueNum += 1
                        self.PreMEM.add_entry(pinst)
                        self.PreIssue.pop_entry(idx)
                    elif not isinstance(pinst.inst, InstructionLoadWord):
                        LWSeq = False

    def alu(self):
        """
        The ALU handles the calculation all non-memory instructions except SLL, SRL, SRA and MUL. All the instructions will take one cycle in ALU. In other words, if the Pre-ALU queue is not empty at the end of cycle N, ALU processes the topmost instruction from the Pre-ALU queue in cycle N+1. The topmost instruction is removed from the Pre-ALU queue before the end of cycle N+1. (Therefore the issue unit will see at least one empty slot in Pre-ALU queue in the beginning of cycle N+2.)
        The processed instruction and its result will be written into the Post-ALU buffer at the end of cycle N+1. Note that this operation will be performed regardless of whether Post-ALU is occupied at the beginning of cycle N+1. In other words, there is no need to check for structural hazard in Post-ALU buffer.
        """
        if self.PreALU.is_empty():
            return
        pinst = self.PreALU.get(0)
        if self.FU.alu is not None and self.FU.alu.is_ready_for_exec():
            self.PreALU.pop_entry(0)
            inst = pinst.inst
            # calc the pinst.result
            rg1 = self.RF.reg_read(self.FU.alu.f_j)
            if inst.type is not Instruction._Types.type_2:
                rg2 = self.RF.reg_read(self.FU.alu.f_k)
            else:
                val = self.FU.alu.f_k
            if isinstance(inst, InstructionAnd):
                pinst.result = rg1 & rg2
            elif isinstance(inst, InstructionNotOr):
                pinst.result = ~ (rg1 | rg2)
            elif isinstance(inst, InstructionSubtractWord):
                pinst.result = rg1 - rg2
            elif isinstance(inst, InstructionAddWord):
                pinst.result = rg1 + rg2
            elif isinstance(inst, InstructionSetOnLessThan):
                pinst.result = 1 if rg1 < rg2 else 0
            elif isinstance(inst, InstructionAddWord2):
                pinst.result = rg1 + val
            elif isinstance(inst, InstructionSubWord2):
                pinst.result = rg1 - val
            elif isinstance(inst, InstructionAnd2):
                pinst.result = rg1 & val
            elif isinstance(inst, InstructionSetOnLessThan2):
                pinst.result = 1 if rg1 < val else 0
                
            self.PostALU.add_entry(pinst)

    def alub(self):
        """
        The ALUB handles SLL, SRL, SRA and MUL. Due to the hardware complexity, it takes two cycles to process SLL, SRL, SRA and MUL in ALUB. In other words, if the Pre-ALUB queue is not empty at the end of cycle N, ALUB processes the topmost instruction, X, from the Pre-ALU queue in cycle N+1 and N+2. The topmost instruction X is removed from the Pre-ALU queue before the end of cycle N+2. (Therefore the issue unit will see at least one empty slot in Pre-ALU queue in the beginning of cycle N+3.) Please note that X remains the topmost instruction at the end of cycle N+1, while being processed.
        The processed instruction and its result will be written into the Post-ALUB buffer at the end of cycle N+2. Note that this operation will be performed regardless of whether the Post-ALUB is occupied at the beginning of cycle N+2.
        """
        if self.PreALUB.is_empty():
            return
        pinst = self.PreALUB.get(0)
        if self.FU.alub is not None and self.FU.alub.is_ready_for_exec():
            pinst.exec_cycle += 1
            if pinst.exec_cycle >= 2:
                # calc the pinst.result
                inst = pinst.inst
                rg1 = self.RF.reg_read(self.FU.alu.f_j)
                val = self.FU.alu.f_k
                # For SLL, SRL, SRA: rg1 is the value to be shifted, rg2 is the shift amount
                if isinstance(inst, InstructionShiftWordLeftLogical):
                    pinst.result = signed_str_to_int(
                        int_to_16bitstr(rg1)[val:] + "0"*val)
                elif isinstance(inst, InstructionShiftWordRightLogical):
                    pinst.result = signed_str_to_int(
                        "0"*val + int_to_16bitstr(rg1)[:val])
                elif isinstance(inst, InstructionShiftWordRightArithmetic):
                    pinst.result = signed_str_to_int(int_to_16bitstr(
                        rg1)[0]*val + int_to_16bitstr(rg1)[:val])
                elif isinstance(inst, InstructionMulWord):
                    rg2 = self.RF.reg_read(self.FU.alu.f_k)
                    pinst.result = signed_str_to_int(
                        str((rg1 * rg2) & 0xFFFFFFFF))
                elif isinstance(inst, InstructionMulWord2):
                    pinst.result = signed_str_to_int(
                        str((rg1 * val) & 0xFFFFFFFF))
                self.PostALUB.add_entry(pinst)
                pinst.exec_cycle = -1

    def mem(self):
        """
        The MEM unit handles LW and SW instructions in Pre-MEM queue. For LW instruction, it takes one cycle to finish. When a LW instruction finishes, the instruction with destination register id and the data will be written to the Post-MEM buffer before the end of cycle. Note that this operation will be performed regardless of whether the Post-MEM is occupied at the beginning of this cycle. For SW instruction, it takes one cycle to write the data to memory. When a SW instruction finishes, nothing would be sent to Post-MEM buffer. When a MEM instruction finishes execution at MEM unit, it is removed from the Pre-MEM queue before the end of cycle.
        """
        sz = self.PreMEM.size()

        for idx in range(sz):
            pinst = self.PreMEM.get(idx)
            inst = pinst.inst
            if isinstance(inst, InstructionLoadWord):
                self.PreMEM.pop_entry(idx)
                # calc the pinst.result
                pinst.result = self.DS.mem_read(
                    inst.op1_val + self.RF.reg_read(inst.op2_val))
                self.PostMEM.add_entry(pinst)
            elif isinstance(inst, InstructionStoreWord):
                self.PreMEM.pop_entry(idx)
                self.DS.mem_write(self.RF.reg_read(
                    inst.op2_val) + inst.op1_val, inst.dest)

    def wb(self):
        """
        WB unit can execute up to three writebacks in one cycle. It updates the Register File based on the content of Post-ALU Buffer, Post-ALUB Buffer, and Post-MEM Buffer. The update is finished before the end of the cycle. The new value will be available at the beginning of next cycle
        """
        # based on the PostALU buffer
        if not self.PostALU.isempty():
            if (self.FU.alu.f_i != self.FU.alub.f_j or self.FU.alub.r_j == False) and (self.FU.alu.f_i != self.FU.alub.f_k or self.FU.alub.r_k == False):
                pinst = self.PostALU.get(0)
                self.PostALU.pop_entry(0)
                self.FU.alu_busy = False
                self.RF.reg_write(pinst.dest, pinst.result)

                if self.FU.alub.q_j == "ALU":
                    self.FU.alub.r_j = True
                if self.FU.alub.q_k == "ALU":
                    self.FU.alub.r_k = True

                self.RF.flush_register_status(pinst.dest)
                pinst.result = None
        # based on the PostALUB buffer
        if not self.PostALUB.isempty():
            if (self.FU.alub.f_i != self.FU.alu.f_j or self.FU.alu.r_j == False) and (self.FU.alub.f_i != self.FU.alu.f_k or self.FU.alu.r_k == False):
                pinst = self.PostALUB.get(0)
                self.PostALUB.pop_entry(0)
                self.FU.alub_busy = False
                self.RF.reg_write(pinst.dest, pinst.result)

                if self.FU.alu.q_j == "ALUB":
                    self.FU.alu.r_j = True
                if self.FU.alu.q_k == "ALUB":
                    self.FU.alu.r_k = True

                self.RF.flush_register_status(pinst.dest)
                pinst.result = None
        # based on the PostMEM buffer
        if not self.PostMEM.isempty():
            # todo check whether there is some problem with the registers related
            self.RF.reg_write(pinst.dest, pinst.result)


class _FUEntry:
    def __init__(self, pip_inst: _PipelineInstEntry, f_i: int = None, f_j: int = None, f_k: int = None, q_j: str = "", q_k: str = ""):
        self.pip_inst = pip_inst
        self.idx = pip_inst.issue_cycle
        self.f_i = f_i   # destination register of the intruction in the FU
        self.f_j = f_j   # source register of the instruction in the FU
        self.f_k = f_k   # source register of the instruction in the FU
        self.q_j = q_j   # FU for the source register j
        self.q_k = q_k   # FU for the source register k
        self.r_j = True if q_j == "" else False  # if f_j is ready
        self.r_k = True if q_k == "" else False  # if f_k is ready

    def is_ready_for_exec(self) -> bool:
        return self.r_j and self.r_k
        # is_ready = False
        # if self.r_j and self.r_k:
        #     is_ready = True
        # return is_ready


# todo: merge the queue and buffer together

class Queue:
    """
    queue that follows FIFO used by 
    Pre-ALU, Pre-ALUB, Pre-MEM
    """

    def __init__(self, name: str, size: int):
        self.comingentries = []
        self.entries = []
        self._size = size
        self._name = name

    def update(self):
        self.entries = self.comingentries

    def add_entry(self, entry: _PipelineInstEntry):
        if len(self.comingentries) < self._size:
            self.comingentries.append(entry)
            return True
        else:
            return False

    def pop_entry(self, idx=0):
        if len(self.entries) == 0:
            return False
        else:
            del (self.comingentries[idx])
            return True

    def __str__(self):
        desc_str = self._name + " Queue:\n"
        for idx in range(self._size):
            desc_str += "\tEntry " + str(idx) + ":"
            if idx < len(self.entries):
                desc_str += str(self.entries[idx]) + "\n"
            else:
                desc_str += "\n"
        return desc_str

    # __ means checking the last cycle entries
    def get(self, idx):
        if idx < len(self.entries):
            return self.entries[idx]

    def size(self):
        return len(self.entries)

    def isempty(self):
        return len(self.entries) == 0

    def isfull(self):
        return len(self.entries) == self._size

    def sync_get(self, idx):
        if idx < len(self.comingentries):
            return self.comingentries[idx]

    def sync_size(self):
        return len(self.comingentries)

    def sync_isempty(self):
        return len(self.comingentries) == 0

    def sync_isfull(self):
        return len(self.comingentries) == self._size


class Buffer:
    """
    Buffer used by 
    Pre-Issue, Post-ALU, Post-ALUB, Post-MEM
    """

    def __init__(self, name: str, size: int):
        self._size = size
        self._name = name
        self._table = []
        self._comingtable = []

    def add_entry(self, entry: _PipelineInstEntry):
        if len(self.comingentries) < self._size:
            self.comingentries.append(entry)
            return True
        else:
            return False

    def update(self):
        self._table = self._comingtable

    def pop_entry(self, idx=0):
        if len(self.entries) == 0:
            return False
        else:
            del (self.comingentries[idx])
            return True

    def get(self, idx):
        if idx < len(self._table):
            return self._table[idx]
        return None

    def __str__(self):
        desc_str = self._name + " Buffer:\n"
        if len(self._table) == 1:
            desc_str += str(self._table[0]) + "\n"
        if self._size >= 2:
            for idx in range(self._size):
                desc_str += "\tEntry " + str(idx) + ":"
                if idx < len(self._table):
                    desc_str += str(self._table[idx]) + "\n"
                else:
                    desc_str += "\n"
        return desc_str

    def sync_get(self, idx):
        return len(self._comingtable[idx])

    def sync_size(self):
        return len(self._comingtable)

    def sync_isempty(self):
        return len(self._comingtable) == 0

    def sync_isfull(self):
        return len(self._comingtable) == self._size

    def get(self, idx):
        return len(self._table[idx])

    def size(self):
        return len(self._table)

    def isempty(self):
        return len(self._table) == 0

    def isfull(self):
        return len(self._table) == self._size


class RegisterFile:
    """
    32 integer registers.
    including the implemnetation of the register status table
    """

    def __init__(self):
        self.size = 32
        self.print_width = 8
        self.R = [0] * self.size
        self._table_RegisterStatus = []
        for idx in range(self.size):
            self._table_RegisterStatus.append(_RegisterAllocationUnit())

    def __str__(self):
        desc_str = 'Registers'
        for idx in range(len(self.R)):
            if idx % self.print_width == 0:
                desc_str += '\nR{}:'.format(str(idx).zfill(2))
            desc_str += '\t' + str(self.R[idx])
        desc_str += '\n'
        return desc_str

    def record_register_status(self, reg_addr: int, fu: str):
        if fu == "ALU":
            self._table_RegisterStatus[reg_addr].inalu = True
        if fu == "ALUB":
            self._table_RegisterStatus[reg_addr].inalub = True

    def is_ready(self, reg_addr: int) -> bool:
        return self._table_RegisterStatus[reg_addr].inalu == False and self._table_RegisterStatus[reg_addr].inalub == False

    def inalu(self, reg_addr) -> bool:
        return self._table_RegisterStatus[reg_addr].inalu

    def inalub(self, reg_addr) -> bool:
        return self._table_RegisterStatus[reg_addr].inalub

    def flush_register_status(self, reg_addr: int):
        for reg_status in self._table_RegisterStatus:
            reg_status.reset()

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
    Data Segment of the memory. Starts from the end of the BREAK of the program and until the end of the file.
    """

    def __init__(self, data_mem):
        self._table = data_mem
        self.print_width = 8
        self._mem_lock = {}
        for addr in data_mem:
            self._mem_lock[addr] = False

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

    def mem_lock(self, mem_addr):
        return self._mem_lock[mem_addr]


class FunctionalUnitStatus:
    """
    Functional Unit Status Table
    ALU   non memory instrucitons 
    ALUB   SLL, SRL, SRA, MUL
    """

    def __init__(self, RF: RegisterFile):
        self.size = 2
        self.alu = None
        self.alub = None
        self.alu_busy = False
        self.alub_busy = False
        self.ref_RF = RF

    def __str__(self):
        desc_str = 'Functional Unit Status Table:\n'
        for rs_entry in self.queue:
            desc_str += '[{}]\n'.format(rs_entry.pip_inst.inst.desc_str)
        # end for
        return desc_str

    def add_entry(self, pinst: _PipelineInstEntry):
        success = False
        dest, s1, s2 = self.decode(pinst)
        qj, qk = "", ""
        if pinst.get_type() == _InstTypes.ALU:
            # not busy and not result D
            if self.alu_busy or self.ref_RF.isready(dest) == False:
                return success
            self.alu_busy = True
            qj = "ALU" if self.ref_RF[s1].inalu() else "ALUB" if self.ref_RF[s1].inalub() else "None"
            if pinst.inst.type != Instruction._Types.type_2:
                qk = "ALU" if self.ref_RF[s2].inalu(
                ) else "ALUB" if self.ref_RF[s2].inalub() else "None"
            self.alu = _FUEntry(pinst, dest, s1, s2, qj, qk)
            # Result D  = dest
            self.ref_RF.record_register_status(dest, "ALU")
            
            success = True
        elif pinst.get_type() == _InstTypes.ALUB:
            if self.alub_busy or self.ref_RF.isready(dest) == False:
                return success
            self.alu_busy = True
            qj = "ALU" if self.ref_RF[s1].inalu(
            ) else "ALUB" if self.ref_RF[s1].inalub() else ""
            if isinstance(pinst.inst, InstructionMulWord):
                qk = "ALU" if self.ref_RF[s2].inalu(
                ) else "ALUB" if self.ref_RF[s2].inalub() else ""
            self.alub = _FUEntry(pinst, dest, s1, s2, qj, qk)
            # Result D  = dest
            self.ref_RF.record_register_status(dest, "ALUB")
            success = True
        elif pinst.get_type() == _InstTypes.SL:
            pass
        return success

    # only decode the ALU and SL instructions
    def decode(self, pinst: _PipelineInstEntry):
        inst = pinst.inst
        dest, op1, op2 = None, None, None
        if pinst.get_type() == _InstTypes.ALU or isinstance(inst, InstructionMulWord):
            if inst.type is Instruction._Types.type_2:
                return inst.dest, inst.op1_val, inst.imm_val
            return inst.dest, inst.op1_val, inst.op2_val
        elif pinst.get_type() == _InstTypes.ALUB:
            if isinstance(inst, InstructionMulWord2):
                return inst.dest, inst.op1_val, inst.imm_val
            return inst.dest, inst.op2_val, inst.sa_val
        elif pinst.get_type() == _InstTypes.SL:
            return inst.dest, inst.op1_val, inst.op2_val
        return dest, op1, op2

    def pop_entry(self, idx=0):
        del (self.queue[idx])