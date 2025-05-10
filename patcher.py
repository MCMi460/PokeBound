from json import loads as json_loads
from time import sleep
from os.path import exists, join
from os import system, name, listdir, remove
from filecmp import cmp
from shutil import rmtree, copytree
from diff_match_patch import diff_match_patch
from pickle import dumps, loads

with open("exclusions.json", "r") as exclusions_json:
    exclusions = json_loads(exclusions_json.read())
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


def clear():
    system("cls" if name == "nt" else "clear")


# Validation functions


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


def reset_translations():
    validate()
    rmtree("translation/")
    copytree("canonical/", "translation/")


# Patcher functions

dmp = diff_match_patch()


def generate_patches():
    validate()
    validate("translation")
    for text_type in ("story", "system"):
        print("%s:" % text_type)
        n = 0
        for file in listdir("canonical/%s/0000" % text_type):
            patch_name = file.replace(".txt", ".patch")
            can = join("canonical/%s/0000" % text_type, file).replace("\\", "/")
            trn = join("translation/%s/0000" % text_type, file).replace("\\", "/")
            ptc = join("patches/%s/0000" % text_type, patch_name).replace("\\", "/")
            if file.startswith("."):
                continue
            if cmp(can, trn):
                if exists(ptc):
                    remove(ptc)
                    print(" - %s" % patch_name)
                continue

            with open(can, "r", encoding="utf8") as src:
                src_text = src.read()
            with open(trn, "r", encoding="utf8") as mod:
                mod_text = mod.read()

            diff = dmp.diff_main(src_text, mod_text)
            dmp.diff_cleanupSemantic(diff)

            patch = dmp.patch_make(src_text, diff)

            with open(ptc, "wb+") as dst:
                dst.write(dumps(patch))

            print(" + %s" % patch_name)
            n += 1
        if n == 0:
            print(" ~")


def apply_patches():  # Warning: Does NOT revert existing changes if no patch file exists
    validate()
    validate("translation")
    for text_type in ("story", "system"):
        for file in listdir("patches/%s/0000" % text_type):
            can = join(
                "canonical/%s/0000" % text_type, file.replace(".patch", ".txt")
            ).replace("\\", "/")
            trn = join(
                "translation/%s/0000" % text_type, file.replace(".patch", ".txt")
            ).replace("\\", "/")
            ptc = join("patches/%s/0000" % text_type, file).replace("\\", "/")
            if file.startswith("."):
                continue

            with open(can, "r", encoding="utf8") as src:
                src_text = src.read()
            with open(ptc, "rb") as mod:
                patch = loads(mod.read())

            mod_text = dmp.patch_apply(patch, src_text)[0]

            with open(trn, "w+", encoding="utf8") as dst:
                dst.write(mod_text)


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
        clear()
        match inp:
            case "1":
                generate_patches()
            case "2":
                apply_patches()
            case "3":
                reset_translations()
            case _:
                pass
        print(
            "MENU:\n"
            + "1: Generate patches\n"
            + "2: Apply patches\n"
            + "3: Reset existing translations (does not affect patches)\n"
            + "0: Exit"
        )
        inp = input("> ")


if __name__ == "__main__":
    if not exists("translation"):
        intro()
    menu()
