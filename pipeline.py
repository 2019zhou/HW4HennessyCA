from mips32 import Instruction, InstructionJump, InstructionJumpRegister, InstructionBranchOnEqual, InstructionBranchOnGreaterThanZero, InstructionBranchOnLessThanZero, InstructionStoreWord, InstructionLoadWord, InstructionShiftWordLeftLogical, InstructionShiftWordRightLogical, InstructionShiftWordRightArithmetic, InstructionAnd, InstructionNotOr, InstructionMulWord, InstructionSubtractWord, InstructionAddWord, InstructionSetOnLessThan, InstructionAddWord2, InstructionSubWord2, InstructionMulWord2, InstructionAnd2, InstructionSetOnLessThan2, signed_str_to_int
from collections import OrderedDict

class Pipeline:
    pc = 64
    cycle = 0
    inst_size = 4
    
    def __init__(self, instr_mem, data_mem):
        self.IF = "" # to do
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
        
        self.FU = FunctionalUnitStatus(self.RF, self.cbd)
        
        self.next_pc = self.pc
        self.is_over = False
    
    def next_cycle(self):
        self.cycle += 1


class _FUEntry:
    def __init__(self, pip_inst: _PipelineInstEntry, f_i: int = None, f_j:int = None, f_k:int = None, q_j: int = None, q_k: int = None, v_j: int = None, v_k: int = None):
        self.pip_inst = pip_inst
        self.idx = pip_inst.issue_cycle
        self.f_i = f_i   # destinateion register of the intruction in the FU
        self.f_j = f_j   # source register of the instruction in the FU
        self.f_k = f_k   # source register of the instruction in the FU
        self.q_j = q_j   # FU to write new values of source register
        self.q_k = q_k   # FU to write new values of source register
        self.r_j = r_j   # if f_j is ready
        self.r_k = r_k   # if f_k is ready
        self.exec_locking = False

    def is_ready_for_exec(self) -> bool:
        is_ready = False
        # if self.q_j is None and self.q_k is None and not self.exec_locking:
        #     # if self.q_j is None and self.q_k is None:
        #     is_ready = True
        if self.r_j and self.r_k and not self.exec_locking:
            is_ready = True
        return is_ready




class FunctionalUnitStatus:
    """
    Functional Unit Status Table
    """

    def __init__(self, RF: RegisterFile, cbd: Dict[int, int]):
        self.size = 10
        self.queue = []
        self.ref_RF = RF
        self.ref_cb = cbd

    def avbl(self):
        avbl = False
        if len(self.queue) < self.size:
            avbl = True
        # end if
        return avbl

    def __str__(self):
        desc_str = 'RS:\n'

        for rs_entry in self.queue:
            desc_str += '[{}]\n'.format(rs_entry.pip_inst.inst.desc_str)
        # end for
        return desc_str

    def flush_from(self, start_point: int):
        for idx, entry in enumerate(list(self.queue)):
            if entry.pip_inst.issue_cycle > start_point:
                self.queue.pop(-1)

    def add_entry(self, pip_inst: _PipelineInstEntry):
        success = False
        if self.avbl():
            vj, vk, qj, qk = self.decode(pip_inst.inst)
            self.queue.append(_RSEntry(pip_inst, vj, vk, qj, qk))
            success = True
        # end if
        return success

    def decode(self, inst: Instruction) -> (int, int, _RegisterAllocationUnit, _RegisterAllocationUnit):

        # instruction Jump do not require decoding in the RS actually
        return vj, vk, qj, qk

    def next_exec_entry(self) -> _RSEntry:
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

    def pop_entry(self, rob_idx):
        for idx in range(len(self.queue)):
            if self.queue[idx].rob_idx == rob_idx:
                self.queue.pop(idx)
                return





class Queue:
    """
    queue that follows FIFO used by 
    Pre-ALU, Pre-ALUB, Pre-MEM
    """
    def __init__(self, name: str, size: int):
        self._size = size
        self._name = name
    
    def __str__(self):
        


class Buffer:
    """
    queue that follows FIFO used by 
    Pre-Issue, Post-ALU, Post-ALUB, Post-MEM
    """
    def __init__(self, name: str, size: int):
        self._size = size
        self._name = name
        self._table = OrderedDict()

    def __str__(self):
        desc_str = self._name + " Buffer:"
        if self._size == 0:
            desc_str += 
            
    def add_entry(self, current_pc: int, target_pc: int, taken=True):
        if len(self._table) >= self.size:
            # if the BTB is full pop the earliest entry and add the new one
            self._table.popitem(last=False)
        self._table[current_pc] = _BTBEntry(current_pc, target_pc, taken)

    def update_mispredict(self, current_pc: int):
        entry = self._table.get(current_pc)
        entry.taken = not entry.taken

    def update_entry(self, current_pc: int, target_pc: int, taken=True):
        _, target, _ = self.lookup_entry(current_pc)
        if target is None:
            # not exists, insert
            self.add_entry(current_pc, target_pc, taken)
        else:
            self._table[current_pc].taken = taken

    def list_entries(self):
        return self._table.keys()

    def lookup_entry(self, pc_val: int) -> (int, int, bool):
        entry = self._table.get(pc_val)

        if entry is None:
            return None, None, False
        else:
            return entry.current_pc, entry.target_pc, entry.taken    



class RegisterFile:
    """
    32 integer registers.
    """

    def __init__(self):
        self.size = 32
        self.print_width = 8
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
