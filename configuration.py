import math


def get_delta(stride, bank_num):
    if stride == 0:
        return [0] * 16

    count = 0
    while stride % 2 == 0:
        count += 1
        stride = stride // 2

    Q = min(int(math.log2(bank_num)), count)
    delta = [0] * 16

    for i in range(16):
        delta[i] = ((i % bank_num) >> (
            int(math.log2(bank_num)) - Q)) % (1 << Q)

    return delta


class Stream:
    def __init__(self, ag_id, sag_id_group, bank_num, stride, multi, ag_stride, ag_direction, scalar_stride_level):
        self.stride = stride
        self.multi = multi
        self.bank_num = bank_num
        self.ag_id = ag_id
        self.sag_id_group = sag_id_group
        self.ag_stride = ag_stride
        self.ag_direction = ag_direction
        self.scalar_stride_level = scalar_stride_level

        if ag_direction == 'channel':
            self.delta = get_delta(stride * multi * ag_stride, bank_num)
        elif ag_direction == 'row':
            self.delta = get_delta(stride * ag_stride, bank_num)
        elif ag_direction == 'col':
            self.delta = get_delta(ag_stride, bank_num)
        elif ag_direction == 'fft_stride_n' or ag_direction == 'fft_stride_1':
            delta = [1] * 16
            delta[0] = 0
            delta[1] = 2
            self.delta = delta


class Bitstream:
    def __init__(self, stream_group):
        self.stream_group = stream_group
        self.delta_table = {}
        self.sag_stride_group = {}
        self.generate()

    def get_stream(self, stream_id):
        return self.stream_group[stream_id]

    def generate(self):
        self.generate_delta_table()
        for stream in self.stream_group:
            self.generate_sag_configuration(stream)

    def generate_delta_table(self):
        for stream in self.stream_group:
            id = stream.ag_id
            self.delta_table[id] = []

            for delta_entry in stream.delta:
                self.delta_table[id].append(delta_entry)

    def generate_sag_configuration(self, stream):
        for scalar_index, sag_id in enumerate(stream.sag_id_group):
            self.generate_sag_stride(sag_id, scalar_index, stream)

    def generate_sag_stride(self, sag_id, scalar_index, stream: Stream):
        direction = stream.ag_direction

        sag_stride = scalar_index * stream.ag_stride

        if direction == 'channel':
            sag_stride_dir = stream.multi * stream.stride * sag_stride
        elif direction == 'row':
            sag_stride_dir = stream.stride * sag_stride
        elif direction == 'col':
            sag_stride_dir = sag_stride
        elif direction == 'fft_stride_n':
            sag_stride = stream.ag_stride * (scalar_index // 2)

            col_addr = stream.ag_stride * (scalar_index % 2)
            row_addr = sag_stride * stream.stride
            sag_stride_dir = col_addr + row_addr
        elif direction == 'fft_stride_1':
            sag_stride = 0
            sag_stride_dir = scalar_index * stream.ag_stride

        self.sag_stride_group[sag_id] = sag_stride, sag_stride_dir
