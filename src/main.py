import argparse
import textwrap
import sys
import os
import re
import io
import struct
import faulthandler
import ndspy.rom as RomReader
import ndspy.lz10 as Lz10

class Text(object):
    header = None
    length = 0
    name = ''
    data = b''

    def __init__(self):
        pass

class PCM(io.BytesIO):
    files = []
    def __init__(self, name, data):
        super(PCM, self).__init__(data)
        self.name = name.replace('data/etext/en/', '').replace('.pcm', '')
        self.header = struct.unpack('<L', self.read(4))[0]
        self.length = struct.unpack('<L', self.read(4))[0]
        self.total = struct.unpack('<L', self.read(4))[0]
        self.id = struct.unpack('<4s', self.read(4))[0].decode()
        if self.id == 'LPCK':
            for i in range(self.total):
                current_offset = self.tell()
                text = Text()
                text.header = struct.unpack('<L', self.read(4))[0]
                text.length = struct.unpack('<L', self.read(4))[0]
                struct.unpack('<L', self.read(4))[0]
                data_length = struct.unpack('<L', self.read(4))[0]
                text.name  = struct.unpack('<16s', self.read(16))[0]
                text.name  = text.name.replace(b'\x00',b'').decode()
                text.data=self.read(data_length)
                self.files.append(text)
                self.seek(current_offset+text.length, os.SEEK_SET)

class NDS(io.BufferedReader):
    ENDSTRING = '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    nds_files = [
        'data/etext/en/e000.pcm',
        'data/etext/en/e100.pcm',
        'data/etext/en/e200.pcm',
        'data/etext/en/etext.pcm'
    ]
    dec_files = []

    def __init__(self, data):
        super(NDS, self).__init__(data)
        rom = RomReader.NintendoDSRom(self.read())
        self.title = rom.name.decode()
        if self.title == 'LAYTON1':
            for file in self.nds_files:
                decoded = Lz10.decompress(rom.getFileByName(file))
                self.dec_files.append(PCM(file, decoded))
            for container in self.dec_files:
                for text in container.files:
                    # Check if output directory exists otherwise create them
                    try:
                        os.stat('output/')
                    except:
                        os.mkdir('output/')
                    try:
                        os.stat('output/'+container.name+'/')
                    except:
                        os.mkdir('output/'+container.name+'/')
                    tmp = open('output/'+container.name+'/'+text.name, 'wb')
                    tmp.write(text.data)
                    tmp.close()
                
        else:
            print("[ERROR] Invalid ROM")
            exit(1)


class Application(argparse.ArgumentParser):
    title = '''
        Professor Layton - Script Extractor
        ----------------------------------------------
        Tool to extract scripts from:
            [NDS] Professor Layton
    '''

    argument_list = [
        {
            'name'      : 'input',
            'nargs'     : '?',
            'type'      : argparse.FileType('rb'),     
            'default'   : sys.stdin,
            'help'      : 'Professor Layton ROM file (.nds)'
        }
    ]

    def __init__(self):
        super(Application, self).__init__()
        self.formatter_class=argparse.RawDescriptionHelpFormatter
        self.description=textwrap.dedent(self.title)

        for argument in self.argument_list:
                self.add_argument(
                argument['name'],
                nargs=argument['nargs'],
                type=argument['type'],
                default=argument['default'],
                help=argument['help']
            )        

        args = self.parse_args()
        if args.input.name != '<stdin>':
            data = NDS(args.input)
        else:
            self.print_help()

if __name__=="__main__":
    app = Application()