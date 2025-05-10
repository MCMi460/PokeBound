from json import loads
from time import sleep
from os.path import exists, join
from os import listdir, remove
from filecmp import cmp
from difflib import unified_diff
from shutil import copytree

with open("exclusions.json", "r") as exclusions_json:
    exclusions = loads(exclusions_json.read())
    exclude_story_files = exclusions["story"]
    exclude_system_files = exclusions["system"]


# Display functions
delay = False


def display(text: str):
    if not delay:
        return print(text)
    text += "\n"
    for char in text:
        print(char, end="", flush=True)
        sleep(0.01)
        if char in ",.:;/\n":
            sleep(0.2)


def wait():
    global delay
    if "skip" in input("[PRESS ENTER TO CONTINUE]").lower():
        delay = False


# Validate canonical tree
def validate(tree: str = "canonical"):
    assert all(
        [
            "%04d.txt" % file in listdir("%s/story/0000" % tree)
            for file in range(676)
            if file not in exclude_story_files
        ]
    )
    assert all(
        [
            "%04d.txt" % file in listdir("%s/system/0000" % tree)
            for file in range(495)
            if file not in exclude_system_files
        ]
    )


# Patcher functions


def generate_patches():
    validate()
    validate("translation")
    for file in listdir("canonical/story/0000"):
        can = join("canonical/story/0000", file)
        trn = join("translation/story/0000", file)
        ptc = join("patches/story/0000", file.replace(".txt", ".patch"))
        if file.startswith("."):
            continue
        if cmp(can, trn):
            if exists(ptc):
                remove(ptc)
            continue

        with open(can, "r", encoding="utf8") as src:
            src_lines = src.readlines()
        with open(trn, "r", encoding="utf8") as mod:
            mod_lines = mod.readlines()

        diff = unified_diff(src_lines, mod_lines, fromfile=can, tofile=trn)

        with open(ptc, "w+", encoding="utf8") as dst:
            dst.writelines(diff)


def apply_patches():
    pass


# User interface functions


def intro():
    display(
        "This seems to be your first time using this program.\n"
        + "In order to continue, you must first extract two NARC files from the base ROM.\n"
        + "For consistency's sake, please use the White 2 ROM.\n"
        + "MD5: 0AFC7974C393265D8CF23379BE232A1C"
    )
    wait()
    display(
        "Please prepare a ROM extrator software (like Nitro Explorer 2, kiwi.ds, etc.)"
    )
    wait()
    display(
        "Extract the NARCs a/0/0/2 and a/0/0/3 and name them system.narc and story.narc respectively."
    )
    wait()
    display("Please open PPTXT.")
    wait()
    display(
        'Open the system.narc in PPTXT and, under the file dropdown menu, select "Export all to Files."'
    )
    wait()
    display("Navigate through the canonical folder and select the system folder.")
    wait()
    display(
        "Now, open story.narc and repeat those steps.\n"
        + "But this time, select the story folder within the canonical folder instead."
    )
    wait()
    display('Have you performed all of these steps? Type "yes" to continue:')
    while "yes" not in input("> ").lower():
        pass

    # Copy to translation tree
    validate()
    copytree("canonical/", "translation/")
    # Apply existing patches
    apply_patches()


def menu():
    inp = ""
    while inp != "0":
        match inp:
            case "1":
                generate_patches()
            case _:
                pass
        print("MENU:\n" + "1: Generate patches\n" + "0: Exit")
        inp = input("> ")


if __name__ == "__main__":
    if not exists("translation"):
        intro()
    menu()
