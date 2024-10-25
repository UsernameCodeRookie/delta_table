from hardware import *
from configuration import *


class GeneratorTest0:
    def __init__(self, bitstream: Bitstream):

        self.bitstream = bitstream
        self.component_group = {}
        self.connection_group = {}
        self.generate_component()
        self.generate_connection()

    def generate_component(self):
        # lsu
        delta_table = self.bitstream.delta_table
        lsu = Lsu(delta_table)
        self.component_group['lsu'] = [lsu]

        # ag
        stream = self.bitstream.get_stream(0)
        ag_id = stream.ag_id
        direction = stream.ag_direction
        multi = stream.multi
        stride = stream.stride
        scalar_stride_level = stream.scalar_stride_level
        ag = Ag(direction, multi, stride, scalar_stride_level)
        self.component_group['ag'] = [ag]

        # sag
        sag_id_group = stream.sag_id_group
        bank_num = stream.bank_num
        for sag_id in sag_id_group:
            sag_stride, sag_stride_dir = self.bitstream.sag_stride_group[sag_id]
            sag = Sag(ag_id, sag_stride, sag_stride_dir,
                      bank_num, scalar_stride_level)

            if self.component_group.get('sag') is None:
                self.component_group['sag'] = []

            self.component_group['sag'].append(sag)

        # spm
        spm = Spm()
        self.component_group['spm'] = [spm]

    def generate_connection(self):
        sag_group = self.component_group['sag']
        ag = self.component_group['ag'][0]
        lsu = self.component_group['lsu'][0]
        spm = self.component_group['spm'][0]

        # connect sag to lsu
        for sag in sag_group:
            sag2lsu2sag = Sag2Lsu2Sag(sag, lsu)

            if self.connection_group.get('sag2lsu2sag') is None:
                self.connection_group['sag2lsu2sag'] = []

            self.connection_group['sag2lsu2sag'].append(sag2lsu2sag)

        # connect ag to sag
        for sag in sag_group:
            ag2sag = Ag2Sag(ag, sag)

            if self.connection_group.get('ag2sag') is None:
                self.connection_group['ag2sag'] = []

            self.connection_group['ag2sag'].append(ag2sag)

        # connect pe to ag
        pe2ag = Pe2Ag(ag, fft_stride_1_pe_in())
        self.connection_group['pe2ag'] = [pe2ag]

        # connect sag to spm
        for sag in sag_group:
            sag2spm = Sag2Spm(sag, spm)
            if self.connection_group.get('sag2spm') is None:
                self.connection_group['sag2spm'] = []
            self.connection_group['sag2spm'].append(sag2spm)

    def update(self):
        for pe2ag in self.connection_group['pe2ag']:
            pe2ag.update()

        for ag in self.component_group['ag']:
            ag.update()

        for ag2sag in self.connection_group['ag2sag']:
            ag2sag.update()

        for sag in self.component_group['sag']:
            sag.update_0()

        for sag2lsu2sag in self.connection_group['sag2lsu2sag']:
            sag2lsu2sag.update()

        for sag in self.component_group['sag']:
            sag.update_1()

        for sag2spm in self.connection_group['sag2spm']:
            sag2spm.update()

    def get_spm_trans(self):
        return self.component_group['spm'][0].get_trans()


class Sim:
    def __init__(self):
        stream = Stream(0, [0, 1, 2, 3], 4, 8, 1, 1, 'fft_stride_1', 0)
        bitstream = Bitstream([stream])
        generator = GeneratorTest0(bitstream)

        self.object = generator

    def run(self):
        self.object.update()


def print_layout(coord_group):
    max_x = max(coord[0] for coord in coord_group) + 1
    max_y = max(coord[1] for coord in coord_group) + 1

    table = [['x' for _ in range(max_y)] for _ in range(max_x)]

    for index, (x, y) in enumerate(coord_group):
        table[x][y] = str(index)

    for row in table:
        print(' '.join(row))


if __name__ == '__main__':
    sim = Sim()

    for i in range(4):
        sim.run()

    trans, trans_old = sim.object.get_spm_trans()

    # print_layout(trans)
