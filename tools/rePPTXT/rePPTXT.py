import typing
from tkinter import Tk, filedialog
from os.path import isfile, join, isdir
from os import listdir
from io import BytesIO, SEEK_END
from struct import unpack, pack
from binascii import unhexlify

Tk().withdraw()

filetypes = (("Narc files", "*.narc"),)

# Display


def out(title: str) -> str:
    print(title)
    return title


# Data
class DataStream(BytesIO):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def read8(self):
        return int(unpack("<?", super().read(1))[0])

    def read16(self):
        return unpack("<H", super().read(2))[0]

    def read32(self):
        return unpack("<I", super().read(4))[0]

    def write8(self, var: int):
        super().write(pack("<?", var))

    def write16(self, var: int):
        super().write(pack("<H", var))

    def write32(self, var: int):
        super().write(pack("<I", var))

    def seek_end(self):
        super().seek(0, SEEK_END)

    def __len__(self):
        return self.getbuffer().nbytes


# Transcribed from the original project PPTXT into Python


class Narc:
    def __init__(self, path: str):
        self.path = path
        assert isfile(path)
        with open(path, "rb") as file:
            self.data = DataStream(file.read())
        self.read()

    def save(self):
        assert isfile(self.path)
        with open(self.path, "wb") as file:
            file.write(self.store().read())

    def read(self):
        self.fileData = []
        self.data.seek(0)
        self.magic = self.data.read32()
        self.unk1 = self.data.read16()
        self.unk2 = self.data.read16()
        self.size = self.data.read32()
        self.headerSize = self.data.read16()
        self.unk3 = self.data.read16()
        self.btaf = self.data.read32()
        self.btafSize = self.data.read32()
        self.numEntries = self.data.read32()
        self.startOffsets = [0] * self.numEntries
        self.endOffsets = [0] * self.numEntries
        for i in range(self.numEntries):
            self.startOffsets[i] = self.data.read32()
            self.endOffsets[i] = self.data.read32()
        self.btnf = self.data.read32()
        self.btnfSize = self.data.read32()
        self.unk4 = self.data.read32()
        self.unk5 = self.data.read32()
        self.gmif = self.data.read32()
        self.gmifSize = self.data.read32()
        for i in range(self.numEntries):
            size = self.endOffsets[i] - self.startOffsets[i]
            temp = [None] * size
            self.fileData.append(DataStream())
            for j in range(size):
                self.fileData[i].write(self.data.read(1))
            for j in range((4 - (size % 4)) % 4):
                self.data.read8()
        return self.data

    def store(self):
        self.data = DataStream()
        self.btafSize = self.gmifSize = 0
        self.startOffsets.clear()
        self.endOffsets.clear()
        offset = 0
        for i in range(self.numEntries):
            self.startOffsets.append(offset)
            offset += len(self.fileData[i])
            self.endOffsets.append(offset)
            offset += (4 - (len(self.fileData[i]) % 4)) % 4
        self.btafSize = 12 + 8 * self.numEntries
        self.gmifSize = offset + 8
        self.size = self.gmifSize + self.btnfSize + self.btafSize + self.headerSize
        self.data.write32(self.magic)
        self.data.write16(self.unk1)
        self.data.write16(self.unk2)
        self.data.write32(self.size)
        self.data.write16(self.headerSize)
        self.data.write16(self.unk3)
        self.data.write32(self.btaf)
        self.data.write32(self.btafSize)
        self.data.write32(self.numEntries)
        for i in range(self.numEntries):
            self.data.write32(self.startOffsets[i])
            self.data.write32(self.endOffsets[i])
        self.data.write32(self.btnf)
        self.data.write32(self.btnfSize)
        self.data.write32(self.unk4)
        self.data.write32(self.unk5)
        self.data.write32(self.gmif)
        self.data.write32(self.gmifSize)
        for i in range(self.numEntries):
            self.fileData[i].seek(0)
            self.data.write(self.fileData[i].read())
            for j in range((4 - (len(self.fileData[i]) % 4)) % 4):
                self.data.write8(0)
        self.data.seek(0)
        return self.data


# Top-level

keys = []
unknowns = []


def get_strings(narc: Narc, m: int, i: int) -> typing.List[str]:
    strings = []
    keys.clear()
    unknowns.clear()
    if i >= 0 and m >= 0:
        stream = narc.fileData[m]
        stream.seek(0)
        sizeSections = [0, 0, 0]
        sectionOffset = [0, 0, 0]
        tableOffsets = {}
        characterCount = {}
        unknown = {}
        encText = {}
        decText = {}
        decText[i] = []

        numSections = stream.read16()
        numEntries = stream.read16()
        sizeSections[0] = stream.read32()
        unk1 = stream.read32()

        if numSections > i:
            for z in range(numSections):
                sectionOffset[z] = stream.read32()
            stream.seek(sectionOffset[i])
            sizeSections[i] = stream.read32()

            tableOffsets[i] = []
            characterCount[i] = []
            unknown[i] = []
            for j in range(numEntries):
                tmpOffset = stream.read32()
                tmpCharCount = stream.read16()
                tmpUnknown = stream.read16()
                tableOffsets[i].append(tmpOffset)
                characterCount[i].append(tmpCharCount)
                unknown[i].append(tmpUnknown)
                unknowns.append(tmpUnknown)

            encText[i] = []
            for j in range(numEntries):
                tmpEncChars = []
                stream.seek(sectionOffset[i] + tableOffsets[i][j])
                for k in range(characterCount[i][j]):
                    tmpChar = stream.read16()
                    tmpEncChars.append(tmpChar)

                encText[i].append(tmpEncChars)
                key = encText[i][j][characterCount[i][j] - 1] ^ 0xFFFF

                k = characterCount[i][j] - 1
                while k >= 0:
                    encText[i][j][k] ^= key
                    if k == 0:
                        keys.append(key)
                    key = ((key >> 3) | (key << 13)) & 0xFFFF
                    k -= 1

                chars = []
                string = ""
                for k in range(characterCount[i][j]):
                    if encText[i][j][k] == 0xFFFF:
                        # chars.append("\\xffff")
                        pass
                    else:
                        if (
                            encText[i][j][k] > 20
                            and encText[i][j][k] <= 0xFFF0
                            and encText[i][j][k] != 0xF000
                            and 0 <= encText[i][j][k] <= 0x10FFFF
                        ):
                            chars.append(chr(encText[i][j][k]))
                        else:
                            num = format(encText[i][j][k], "x")
                            for l in range(4 - len(num)):
                                num = "0" + num
                            chars.append(r"\x" + num)
                        string += chars[k]
                strings.append(string)
                decText[i].append(chars)
    return strings


def parse_string(string: str, entry_id: int):
    chars = []
    for i in range(len(string)):
        if string[i] != "\\":
            chars.append(ord(string[i]))
        else:
            if (i + 2 < len(string)) and string[i + 2] == "{":
                chars.append(ord(string[i]))
            else:
                tmp = ""
                for j in range(4):
                    tmp += string[i + j + 2]
                i += 5
                chars.append(unpack("<H", unhexlify(tmp))[0])
    chars.append(0xFFFF)
    key = keys[entry_id]
    # key = 0x7C89
    for i in range(len(chars)):
        chars[i] ^= key
        key = ((key << 3) | (key >> 13)) & 0xFFFF
    return chars


def make_section(strings: typing.List[str], numEntries: int):
    data = []
    size = 0
    offset = 4 + 8 * numEntries
    unk1 = 0x100
    for i in range(numEntries):
        data.append(parse_string(strings[i], i))
        size += len(data[i]) * 2
    if size % 4 == 2:
        size += 2
        tmpKey = keys[numEntries - 1]
        for i in range(len(data[numEntries - 1])):
            tmpKey = ((tmpKey << 3) | (tmpKey >> 13)) & 0xFFFF
        data[numEntries - 1].append(0xFFFF ^ tmpKey)
    size += offset
    # section = [0] * size
    ds = DataStream()
    ds.write(b"0" * size)
    ds.seek(0)
    ds.write32(size)
    for i in range(numEntries):
        charCount = len(data[i])
        ds.write32(offset)
        ds.write16(charCount)
        ds.write16(unknowns[i])
        offset += charCount * 2
    for i in range(numEntries):
        for j in range(len(data[i])):
            ds.write16(data[i][j])
    ds.seek(0)
    return ds.read()


def save_narc():
    for each in ((system_narc, system), (story_narc, story)):
        narc = each[0]
        for i in range(2):
            work_path = join(each[1], "%04d" % i)
            for entry in listdir(work_path):
                file_path = join(work_path, entry)
                if file_path.startswith(".") or not file_path.endswith(".txt"):
                    continue

                # m = narc Entry, i=type
                m = int(entry.replace(".txt", ""))
                print(i, m, file_path)

                with open(file_path, "r", encoding="utf-8") as file:
                    string = file.read()

                if "\r\n" in string:
                    text = string.split("\r\n")
                elif "\r" in string:
                    text = string.split("\r")
                else:
                    text = string.split("\n")

                oText = get_strings(narc, m, i)
                stream = narc.fileData[m]
                stream.seek(0)
                sizeSections = [0, 0, 0]
                sectionOffset = [0, 0, 0]
                newsizeSections = [0, 0, 0]
                newsectionOffset = [0, 0, 0]
                numSections = stream.read16()
                numEntries = stream.read16()
                sizeSections[0] = stream.read32()
                unk1 = stream.read32()
                if i < numSections:
                    if len(text) < numEntries:
                        print("Skipping %s/%s due to too few lines" % (i, m))
                    else:
                        newEntry = make_section(text, numEntries)
                        if i == 0:
                            for z in range(numSections):
                                sectionOffset[z] = stream.read32()
                            for z in range(numSections):
                                stream.seek(sectionOffset[z])
                                sizeSections[z] = stream.read32()
                            newsizeSections[0] = len(newEntry)
                            stream.seek(4)
                            stream.write32(newsizeSections[0])
                            if numSections == 2:
                                newsectionOffset[1] = (
                                    newsizeSections[0] + sectionOffset[0]
                                )
                                stream.seek(0x10)
                                stream.write32(newsectionOffset[1])
                            # Setup for my best replica of behavior
                            section2 = []
                            narc.fileData[m].seek(0)
                            narc.fileData[m] = narc.fileData[m].read()
                            if numSections == 2:
                                # narc.fileData[m].seek(sectionOffset[1])
                                # for j in range(sizeSections[1]):
                                #    section2.append(narc.fileData[m].read8())
                                section2 = narc.fileData[m][
                                    sectionOffset[1] : sectionOffset[1]
                                    + sizeSections[1]
                                ]
                            ds = DataStream()
                            ds.write(
                                narc.fileData[m][: sectionOffset[0]]
                                + narc.fileData[m][
                                    sectionOffset[0]
                                    + sizeSections[0]
                                    + sizeSections[1] :
                                ]
                            )
                            narc.fileData[m] = ds
                            narc.fileData[m].write(newEntry)
                            if numSections == 2:
                                narc.fileData[m].write(section2)
                        elif numSections == 2:
                            sizeSections = [0, 0, 0]
                            sectionOffset = [0, 0, 0]
                            stream.seek(2)
                            numEntries = stream.read16()
                            stream.seek(0xC)
                            for z in range(numSections):
                                sectionOffset[z] = stream.read32()
                            for z in range(numSections):
                                stream.seek(sectionOffset[z])
                                sizeSections[z] = stream.read32()
                            narc.fileData[m].seek(0)
                            narc.fileData[m] = narc.fileData[m].read()
                            ds = DataStream()
                            ds.write(
                                narc.fileData[m][: sectionOffset[1]]
                                + narc.fileData[m][sectionOffset[1] + sizeSections[1] :]
                            )
                            narc.fileData[m] = ds
                            narc.fileData[m].write(newEntry)
        narc.save()


# User interface

if __name__ == "__main__":
    try:
        title = out("Please select the system.narc")
        system_path = filedialog.askopenfilename(title=title, filetypes=filetypes)
        assert isfile(system_path)
        system_narc = Narc(system_path)
        title = out("Please select the story.narc")
        story_path = filedialog.askopenfilename(title=title, filetypes=filetypes)
        assert isfile(story_path)
        story_narc = Narc(story_path)
    except AssertionError as err:
        err.add_note("Maybe you didn't select a .narc file?")
        raise err

    title = out("Please select the translation/ directory")
    upd_path = filedialog.askdirectory(title=title)
    story = join(upd_path, "story")
    system = join(upd_path, "system")

    try:
        assert isdir(join(story, "0000"))
        assert isdir(join(story, "0001"))
        assert isdir(join(system, "0000"))
        assert isdir(join(system, "0000"))
    except AssertionError as err:
        err.add_note("Invalid directory format detected!")
        raise err

    print("Importing files to NARCs...")

    save_narc()
