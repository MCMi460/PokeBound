import typing
from tkinter import Tk, filedialog
from os.path import isfile, join, isdir
from os import listdir
from io import BytesIO
from struct import unpack

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
        return unpack("<h", super().read(2))[0]

    def read32(self):
        return unpack("<i", super().read(4))[0]


class Narc:
    def __init__(self, path: str):
        assert isfile(path)
        with open(path, "rb") as file:
            self.data = DataStream(file.read())

    def __rshift__(self, other):  # >>, read
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
            # self.fileData.append(temp)
            for j in range(size):
                # self.fileData[i][j] = self.data.read8()
                self.fileData[i].write(self.data.read(1))
            for j in range((4 - (size % 4)) % 4):
                self.data.read8()
        return self.data

    def __lshift__(self, other):  # <<, store
        pass


# Top-level


def get_strings(
    narc: Narc, m: int, i: int
) -> typing.List[
    str
]:  # This does NOT work, and the worst part is how difficult it will be to find the error.
    strings = []
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
        print(numEntries)
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
                            chars.append(str(encText[i][j][k]))
                        else:
                            num = hex(encText[i][j][k])
                            for l in range(4 - len(num)):
                                num = "0" + num
                            chars.append("\\x" + num)
                        string += chars[k]
                strings.append(string)
                decText[i].append(chars)
    return strings


def save_narc():
    for i in range(2):
        work_path = join(story, "%04d" % i)
        for entry in listdir(work_path):
            file_path = join(work_path, entry)
            if file_path.startswith(".") or not file_path.endswith(".txt"):
                continue

            # m = narc Entry, i=type
            m = int(entry.replace(".txt", ""))
            print(i, m, file_path)

            with open(file_path, "r", encoding="utf8") as file:
                string = file.read()

            if "\r\n" in string:
                text = string.split("\r\n")
            elif "\r" in string:
                text = string.split("\r")
            else:
                text = string.split("\n")


# User interface

if __name__ == "__main__":
    try:
        title = out("Please select the system.narc")
        system_narc = filedialog.askopenfilename(title=title, filetypes=filetypes)
        assert isfile(system_narc)
        narc = Narc(system_narc)
        narc.__rshift__("whatever")
        print(get_strings(narc, 0, 0))
        quit()
        title = out("Please select the story.narc")
        story_narc = filedialog.askopenfilename(title=title, filetypes=filetypes)
        assert isfile(story_narc)
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

    print(upd_path)
