import math


class Ag:
    def __init__(self, direction, multi, stride, scalar_stride_level):
        self.multi = multi
        self.stride = stride
        self.direction = direction
        self.scalar_stride_level = scalar_stride_level

    def cal_ag_index(self):
        if self.direction == 'channel':
            self.ag_index = self.channel_idx
        elif self.direction == 'row' or self.direction == 'fft_stride_n' or self.direction == 'fft_stride_1':
            self.ag_index = self.channel_idx * self.multi + self.row_idx
        elif self.direction == 'col':
            self.ag_index = self.channel_idx * self.multi * \
                self.stride + self.row_idx * self.stride + self.col_idx

    def cal_ag_linear_addr(self):
        self.ag_linear_addr = self.channel_idx * self.multi * \
            self.stride + self.row_idx * self.stride + self.col_idx

    def set_input(self, channel_idx, row_idx, col_idx):
        self.channel_idx = channel_idx
        self.row_idx = row_idx
        self.col_idx = col_idx

    def get_ag_index(self):
        return self.ag_index

    def get_ag_linear_addr(self):
        return self.ag_linear_addr

    def update(self):
        self.cal_ag_index()
        self.cal_ag_linear_addr()


class Sag:
    def __init__(self, ag_id, sag_stride, sag_stride_dir, bank_num, scalar_stride_level):
        self.ag_id = ag_id
        self.sag_stride = sag_stride
        self.sag_stride_dir = sag_stride_dir
        self.scalar_stride_level = scalar_stride_level

        self.bank_num = bank_num

    def set_ag_index(self, ag_index):
        self.ag_index = ag_index

    def set_ag_linear_addr(self, ag_linear_addr):
        self.ag_linear_addr = ag_linear_addr

    def cal_sag_index(self):
        self.sag_index = self.ag_index + self.sag_stride >> self.scalar_stride_level

    def cal_linear_addr(self):
        self.linear_addr = self.ag_linear_addr + self.sag_stride_dir

    def cal_spm_addr(self):
        self.spm_row_index = self.linear_addr // self.bank_num
        self.spm_col_index = (self.linear_addr +
                              self.sag_delta) % self.bank_num
        self.spm_col_index_old = self.linear_addr % self.bank_num

        print(self.spm_row_index, self.spm_col_index, self.linear_addr)

    def set_sag_delta(self, sag_delta):
        self.sag_delta = sag_delta

    def update_0(self):
        self.cal_sag_index()

    def update_1(self):
        self.cal_linear_addr()
        self.cal_spm_addr()

    def get_spm_addr(self):
        return self.spm_row_index, self.spm_col_index

    def get_sag_index(self):
        return self.sag_index

    def get_ag_id(self):
        return self.ag_id

    def get_spm_addr(self):
        return self.spm_row_index, self.spm_col_index, self.spm_col_index_old


class Lsu:
    def __init__(self, delta_table):
        self.delta_table = delta_table

    def get_ag_delta_table(self, ag_id):
        return self.delta_table[ag_id]


class Spm:
    def __init__(self):
        self.trans = []
        self.trans_old = []

    def add_transaction(self, row_index, col_index):
        self.trans.append((row_index, col_index))

    def add_transaction_old(self, row_index, col_index_old):
        self.trans_old.append((row_index, col_index_old))

    def get_trans(self):
        return self.trans, self.trans_old


class Ag2Sag:
    def __init__(self, ag: Ag, sag: Sag):
        self.ag = ag
        self.sag = sag

    def update(self):
        ag_index = self.ag.ag_index
        ag_linear_addr = self.ag.ag_linear_addr

        self.sag.set_ag_index(ag_index)
        self.sag.set_ag_linear_addr(ag_linear_addr)


def inc_k(i, j, k):
    k += 4

    if k >= 8:
        j = 1

    return i, j, k


class fft_stride_1_pe_in:
    def __init__(self):
        self.k = [0, 4, 0, 4]
        self.j = [0, 0, 1, 1]
        self.cycle = 0

    def __call__(self, i, j, k):

        result = 0, self.j[self.cycle], self.k[self.cycle]

        self.cycle += 1

        return result


class Pe2Ag:
    def __init__(self, ag: Ag, hook=inc_k):
        self.ag = ag
        self.hook = hook

        self.i = 0
        self.j = 0
        self.k = 0

    def update(self):
        self.i, self.j, self.k = self.hook(self.i, self.j, self.k)
        self.ag.set_input(self.i, self.j, self.k)


class Sag2Lsu2Sag:
    def __init__(self, sag: Sag, lsu: Lsu):
        self.sag = sag
        self.lsu = lsu

    def update(self):
        sag_index = self.sag.get_sag_index()
        ag_id = self.sag.get_ag_id()

        delta_table = self.lsu.get_ag_delta_table(ag_id)
        delta_entry = delta_table[sag_index]

        self.sag.set_sag_delta(delta_entry)


class Sag2Spm:
    def __init__(self, sag: Sag, spm: Spm):
        self.sag = sag
        self.spm = spm

    def update(self):
        spm_row_index, spm_col_index, spm_col_index_old = self.sag.get_spm_addr()
        self.spm.add_transaction(spm_row_index, spm_col_index)
        self.spm.add_transaction_old(spm_row_index, spm_col_index_old)
