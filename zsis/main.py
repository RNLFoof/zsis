import os
from datetime import datetime

from PIL import ImageFile

from zsis.classes.SourcerSettings import SourcerSettings

ImageFile.LOAD_TRUNCATED_IMAGES = True


# Setting it up with these values:
# Name to color hash
# Color hash to file hashes
# File hashes to paths

# Could probably set up a n2p in memory for simplicity







hashsettingsfordeletion = SourcerSettings(
    10,
    10,
    7,  # 6 had 7122 items
    True,
    True,
    2
)














def genn2p(settings, startingwith="", settingsrepstr=None, n2ch=None, ch2fh=None, fh2p=None):
    if not settingsrepstr:
        settingsrepstr = get_settings_rep_str(settings)
    if not n2ch:
        n2ch = load(f"n2ch{settingsrepstr}.pkl", {})
    if not ch2fh:
        ch2fh = load(f"ch2fh{settingsrepstr}.pkl", {})
    if not fh2p:
        fh2p = load(f"fh2p.pkl", {})

    n2p = {}
    items = n2ch.items()
    n = 0
    starttime = datetime.utcnow()

    for name, colorhash in items:
        progress.displayprogressreplacements(n, len(items), f"genning n2p starting with " + startingwith,
                                             starttime=starttime)
        n += 1
        if startingwith and not name.startswith(startingwith):
            continue
        if colorhash not in ch2fh:
            continue
        filehashes = ch2fh[colorhash]

        s = set()
        filehashesset = set()
        for filehash in filehashes:
            if filehash in fh2p:
                filehashesset.add(filehash)
                paths = fh2p[filehash]
                # print(name, colorhash, len(filehashes), filehash, paths)
                for path in paths:
                    s.add(path)
        # if len(s) > 100:
        #     print("WAAAA")
        #     # s = set()
        #     # for name, colorhash in items:
        #     #     s.add(colorhash)
        #     print("name", name)
        #     print("colorhash", colorhash)
        #     print("filehashes", filehashesset)
        #     print("paths", s)
        #     # input()
        n2p[name] = list(s)
    progress.displayprogressreplacements(n, len(items), f"genning n2p starting with " + startingwith,
                                         starttime=starttime)
    return n2p


def deleterecordsfrompath(basedir, settings, onlyiffilewasdeleted):
    settingsrepstr = get_settings_rep_str(settings)
    n2ch = load(f"n2ch{settingsrepstr}.pkl", {})
    n2fh = load(f"n2fh.pkl", {})
    starttime = datetime.utcnow()

    for working in [n2ch, n2fh]:
        items = dict(working).items()
        n = 0

        if onlyiffilewasdeleted:
            existingnames = set()
            for root, dirs, files in list(os.walk(basedir)):
                for nn, file in enumerate(files):
                    fullpath = os.path.join(root, file)  # Absolute path to the file we're fucking with
                    refname = get_ref_name(fullpath)
                    existingnames.add(refname)

        for name, hash in items:
            progress.displayprogressreplacements(n, len(items), f"deleting records from {basedir}", starttime=starttime)
            n += 1

            if name.startswith(basedir) and (not onlyiffilewasdeleted or name not in existingnames):
                print("About to remove", name)
                del working[name]

    save(f"n2ch{settingsrepstr}.pkl", n2ch)
    save(f"n2fh.pkl", n2fh)


# Delete hashes then do them again
def redohashes(basedir, settings, destroyevildoers, addsources, maxerrors=1):
    deleterecordsfrompath(basedir, settings, False)
    print("___")
    daves_stupid_backend_function(basedir, settings, destroyevildoers, addsources, maxerrors=maxerrors)
    print("___")


# Delete deleted image hashes then do them again
def cacheredohashes(basedir, settings, destroyevildoers, addsources, maxerrors=1):
    deleterecordsfrompath(basedir, settings, True)
    print("___")
    daves_stupid_backend_function(basedir, settings, destroyevildoers, addsources, maxerrors=maxerrors)
    print("___")


# Add missing hashes
def updatehashes(basedir, settings, destroyevildoers, addsources, maxerrors=1):
    daves_stupid_backend_function(basedir, settings, destroyevildoers, addsources, maxerrors=maxerrors)
    print("___")


# Add missing hashes and remove ones that no longer exist
def updateandtrimhashes(basedir, settings, destroyevildoers, addsources, maxerrors=1):
    deleterecordsfrompath(basedir, settings, True)
    print("___")
    daves_stupid_backend_function(basedir, settings, destroyevildoers, addsources, maxerrors=maxerrors)
    print("___")




if __name__ == "__main__":
    with Sourcer(hashsettingsfordeletion) as sourcer:
        reporter = sourcer.catalog_directory(r"S:\Images\Misc", add_paths_to_sources=True)
        print(reporter)
        # sourcer.add_sources(r"S:\Games\Normal stuff\Danganronpa 3\epic greentexts\loli recycle bin.png", ["1", "2", "3"]
        #                     , True)
