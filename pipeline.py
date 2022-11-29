from mips32 import Instruction, InstructionJump, InstructionJumpRegister, InstructionBranchOnEqual, InstructionBranchOnGreaterThanZero, InstructionBranchOnLessThanZero, InstructionStoreWord, InstructionLoadWord, InstructionShiftWordLeftLogical, InstructionShiftWordRightLogical, InstructionShiftWordRightArithmetic, InstructionAnd, InstructionNotOr, InstructionMulWord, InstructionSubtractWord, InstructionAddWord, InstructionSetOnLessThan, InstructionAddWord2, InstructionSubWord2, InstructionMulWord2, InstructionAnd2, InstructionSetOnLessThan2, InstructionNoOperation, InstructionBreakpoint
from collections import OrderedDict
from enum import Enum


class _InstTypes(Enum):
    SL = 1
    ALU = 2
    BRCH = 3
    UKNW = 4


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
        self.fetch_cycle = -1
        self.issue_cycle = -1
        self.exec_cycle = -1
        self.wb_cycle = -1
        self.is_issued = False
        self.is_wbed = False
        self.is_execed = False

    # def issue(self, cycle):
    #     """
    #     when the instruction being issued, decoding should happened
    #     :param cycle:
    #     :return:
    #     """
    #     self.issue_cycle = cycle
    #     self.is_issued = True

    def get_type(self) -> _InstTypes:
        branch_inst_set = (InstructionJump, InstructionJumpRegister,
                           InstructionBranchOnEqual,
                           InstructionBranchOnGreaterThanZero,
                           InstructionBranchOnLessThanZero)
        sl_inst_set = (InstructionStoreWord, InstructionLoadWord)
        alu_inst_set = (InstructionShiftWordLeftLogical, InstructionShiftWordRightLogical, InstructionShiftWordRightArithmetic, InstructionAnd, InstructionNotOr, InstructionMulWord,
                        InstructionSubtractWord, InstructionAddWord, InstructionSetOnLessThan, InstructionAddWord2, InstructionSubWord2, InstructionMulWord2, InstructionAnd2, InstructionSetOnLessThan2)

        if isinstance(self.inst, alu_inst_set):
            inst_type = _InstTypes.ALU
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
        self.PreIssue = Buffer("Pre-Issue", 4)
        self.PreALU = Queue("Pre-ALU", 2)
        self.PostALU = Buffer("Post-ALU", 1)
        self.PreALUB = Queue("Pre-ALUB", 2)
        self.PostALUB = Buffer("Post-ALUB", 1)
        self.PreMEM = Queue("Pre-MEM", 2)
        self.PostMEM = Buffer("Post-MEM", 1)

        self.inst_mem = inst_mem
        self.RF = RegisterFile()
        self.DS = DataSegment(data_mem)

        self.FU = FunctionalUnitStatus(self.RF)

        self.next_pc = self.pc
        self.is_over = False

    def next_cycle(self):
        self.cycle += 1

        # fetch and decode
        self.fetch()
        # issue
        self.issue()

    def snapshotifunit(self):
        desc_str = "IF Unit:\n\tWaiting Instruction: \n"
        desc_str += "\tExecuted Instruction: \n"
        return desc_str

    def fetch(self):
        """
        Instruction Fetch unit can fetch and decode at most two instructions at each cycle (in program order). The unit should check all the following conditions before it can fetch further instructions.
        1. If the fetch unit is stalled at the end of previous cycle, no instruction can be fetched at the current cycle. The fetch unit can be stalled due to a branch instruction
        2. If there is no empty slot in the Pre-issue buffer at the end of the previous cycle, no instruction can be fetched at the current cycle.
        3. If there is only one empty slot in the Pre-issue buffer at the end of the previous cycle, only one instruction can be fetched at the current cycle.
        """

        for idx in range(2):
            # check if there is no empty slot in the Pre-issue buffer
            if self.PreIssue.is_full():
                break
            # fetch instruction
            next_inst_to_fetch = self.inst_mem.get(self.pc, None)
            pinst = _PipelineInstEntry(next_inst_to_fetch)
            # decode instruction and put it into Pre-Issue buffer
            if not isinstance(pinst.inst, (InstructionNoOperation, InstructionBreakpoint)):
                self.FU.add_entry(pinst)
                if pinst.get_type() == _InstTypes.BRCH:
                    # stall the fetch unit
                    break

        return

        pipline_inst_entry = _PipelineInstEntry(inst)

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
        pass

    def alu(self):
        """
        The ALU handles the calculation all non-memory instructions except SLL, SRL, SRA and MUL. All the instructions will take one cycle in ALU. In other words, if the Pre-ALU queue is not empty at the end of cycle N, ALU processes the topmost instruction from the Pre-ALU queue in cycle N+1. The topmost instruction is removed from the Pre-ALU queue before the end of cycle N+1. (Therefore the issue unit will see at least one empty slot in Pre-ALU queue in the beginning of cycle N+2.)
        The processed instruction and its result will be written into the Post-ALU buffer at the end of cycle N+1. Note that this operation will be performed regardless of whether Post-ALU is occupied at the beginning of cycle N+1. In other words, there is no need to check for structural hazard in Post-ALU buffer.
        """
        pass

    def alub(self):
        """
        The ALUB handles SLL, SRL, SRA and MUL. Due to the hardware complexity, it takes two cycles to process SLL, SRL, SRA and MUL in ALUB. In other words, if the Pre-ALUB queue is not empty at the end of cycle N, ALUB processes the topmost instruction, X, from the Pre-ALU queue in cycle N+1 and N+2. The topmost instruction X is removed from the Pre-ALU queue before the end of cycle N+2. (Therefore the issue unit will see at least one empty slot in Pre-ALU queue in the beginning of cycle N+3.) Please note that X remains the topmost instruction at the end of cycle N+1, while being processed.
        The processed instruction and its result will be written into the Post-ALUB buffer at the end of cycle N+2. Note that this operation will be performed regardless of whether the Post-ALUB is occupied at the beginning of cycle N+2.
        """
        pass

    def mem(self):
        """
        The MEM unit handles LW and SW instructions in Pre-MEM queue. For LW instruction, it takes one cycle to finish. When a LW instruction finishes, the instruction with destination register id and the data will be written to the Post-MEM buffer before the end of cycle. Note that this operation will be performed regardless of whether the Post-MEM is occupied at the beginning of this cycle. For SW instruction, it takes one cycle to write the data to memory. When a SW instruction finishes, nothing would be sent to Post-MEM buffer. When a MEM instruction finishes execution at MEM unit, it is removed from the Pre-MEM queue before the end of cycle.
        """
        pass

    def wb(self):
        """
        WB unit can execute up to three writebacks in one cycle. It updates the Register File based on the content of Post-ALU Buffer, Post-ALUB Buffer, and Post-MEM Buffer. The update is finished before the end of the cycle. The new value will be available at the beginning of next cycle
        """
        pass


class _FUEntry:
    def __init__(self, pip_inst: _PipelineInstEntry, f_i: int = None, f_j: int = None, f_k: int = None, q_j: str = "", q_k: str = ""):
        self.pip_inst = pip_inst
        self.idx = pip_inst.issue_cycle
        self.f_i = f_i   # destination register of the intruction in the FU
        self.f_j = f_j   # source register of the instruction in the FU
        self.f_k = f_k   # source register of the instruction in the FU
        self.q_j = q_j      # FU for the source register j
        self.q_k = q_k   # FU for the source register k
        self.r_j = True if q_j == "" else False  # if f_j is ready
        self.r_k = True if q_k == "" else False # if f_k is ready
        self.busy = False

    def is_ready_for_exec(self) -> bool:
        is_ready = False
        # if self.q_j is None and self.q_k is None and not self.exec_locking:
        #     # if self.q_j is None and self.q_k is None:
        #     is_ready = True
        if self.r_j and self.r_k and not self.busy:
            is_ready = True
        return is_ready


class Queue:
    """
    queue that follows FIFO used by 
    Pre-ALU, Pre-ALUB, Pre-MEM
    """

    def __init__(self, name: str, size: int):
        self.entries = []
        self._size = size
        self._name = name

    def add_entry(self, entry: _PipelineInstEntry):
        if len(self.entries) < self._size:
            self.entries.append(entry)
            return True
        else:
            return False

    def pop_entry(self):
        if len(self.entries) == 0:
            return False
        else:
            del (self.entries[0])
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

    def size(self):
        return len(self.entries)

    def isempty(self):
        return len(self.entries) == 0

    def isfull(self):
        return len(self.entries) == self._size


class Buffer:
    """
    Buffer used by 
    Pre-Issue, Post-ALU, Post-ALUB, Post-MEM
    """

    def __init__(self, name: str, size: int):
        self._size = size
        self._name = name
        self._table = []

    def add_entry(self, entry: _PipelineInstEntry):
        if len(self._table) >= self.size:
            self._table.pop()
        self._table.append(entry)

    def pop_entry(self):
        self._table.pop()

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

    def inalu(self, reg_idx) -> bool:
        return self._table_RegisterStatus[reg_idx].inalu

    def inalub(self, reg_idx) -> bool:
        return self._table_RegisterStatus[reg_idx].inalub

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
        self.queue = []
        self.ref_RF = RF

    def __str__(self):
        desc_str = 'Functional Unit Status Table:\n'
        for rs_entry in self.queue:
            desc_str += '[{}]\n'.format(rs_entry.pip_inst.inst.desc_str)
        # end for
        return desc_str

    # def flush_from(self, start_point: int):
    #     for idx, entry in enumerate(list(self.queue)):
    #         if entry.pip_inst.issue_cycle > start_point:
    #             self.queue.pop(-1)

    def add_entry(self, pip_inst: _PipelineInstEntry):
        success = False
        if self.avbl():
            dest, s1, s2 = self.decode(pip_inst.inst)
            qj = "ALU" if self.ref_RF[s1].inalu(
            ) else "ALUB" if self.ref_RF[s1].inalub() else "None"
            qk = "ALU" if self.ref_RF[s1].inalu(
            ) else "ALUB" if self.ref_RF[s1].inalub() else "None"
            self.queue.append(_FUEntry(pip_inst, dest, s1, s2, qj, qk))
            success = True
        return success

    def decode(self, inst: Instruction):
        dest, op1, op2 = None, None, None
        if isinstance(inst, InstructionAddWord):

            # instruction Jump do not require decoding in the FU actually
        return dest, op1, op2

    def next_exec_entry(self) -> _FUEntry:
        next_inst = None
        for rs_inst_entry in self.queue:
            if rs_inst_entry.is_ready_for_exec():
                next_inst = rs_inst_entry
                break

        return next_inst

    def receive_wb(self, rob_idx, value):
        # for idx, rs_entry in enumerate(self.queue):
        #     if rs_entry.q_j == rob_idx:
        #         rs_entry.v_j = value
        #         rs_entry.q_j = None
        #     if rs_entry.q_k == rob_idx:
        #         rs_entry.v_k = value
        #         rs_entry.q_k = None
        pass

    def pop_entry(self, rob_idx):
        for idx in range(len(self.queue)):
            if self.queue[idx].rob_idx == rob_idx:
                self.queue.pop(idx)
                return
