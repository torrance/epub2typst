import copy
from pathlib import Path
from zipfile import ZipFile

from bs4 import BeautifulSoup, NavigableString, element


class Translator:
    def __init__(self, path, verbose=True):
        z = ZipFile(path)
        MIMETYPE = z.open("mimetype").read().decode().strip()
        print(f"MIMETYPE: {MIMETYPE}")
        assert MIMETYPE == "application/epub+zip"

        container = BeautifulSoup(z.open("META-INF/container.xml"), "lxml-xml")
        ROOTFILE = container.find("rootfiles").find("rootfile")["full-path"]
        print(f"ROOTFILE: {ROOTFILE}")

        # All paths from the OPF file are with respect to the root file
        ROOTPATH = Path(ROOTFILE).parent

        opf = BeautifulSoup(z.open(ROOTFILE), "lxml-xml")
        chapters = []
        for itemref in opf.find("spine").find_all("itemref"):
            chapter = ROOTPATH / opf.find("manifest").find("item", id=itemref["idref"])["href"]
            chapters.append(str(chapter))

        print("CHAPTERS:")
        for i, chapter in enumerate(chapters):
            print(f"{i: 5d}. {chapter}")

        self.chapters = [
            BeautifulSoup(z.open(chapter), "lxml-xml") for chapter in chapters
        ]
        self.rules = []
        self.ignore("body")
        self.verbose = verbose

    def __str__(self):
        s = "\n\n".join(
            [self._translate(chapter.find("body")) for chapter in self.chapters]
        )

        # Remove double spaces and triplicate (or greater) new lines
        while s != s.replace("  ", " ").replace("\n\n\n", "\n\n"):
            s = s.replace("  ", " ").replace("\n\n\n", "\n\n")

        return s

    def __getitem__(self, idx):
        t = copy.copy(self)
        t.chapters = copy.deepcopy(self.chapters[idx])
        return t

    def add_rule(self, tag, before="", after="", fn=lambda x: x):
        self.rules.append((tag, before, after, fn))

    def ignore(self, tag):
        self.add_rule(tag)

    def raw(self):
        return "\n\n".join(
            [chapter.find("body").prettify() for chapter in self.chapters]
        )

    def _translate(self, node):
        if type(node) is NavigableString:
            # Escape special characters from strings
            return (
                str(node.string)
                .strip("\n\r")
                .replace("*", "\\*")
                .replace("_", "\\_")
                .replace("#", "\\#")
                .replace("$", "\\$")
                .replace("[", "\\[")
                .replace("]", "\\]")
                .replace("@", "\\@")
                .replace("<", "\\<")
                .replace(">", "\\>")
            )
        elif type(node) is element.Comment:
            # Ignore comments
            return

        # Otherwise search rules for _first_ matching rule
        for tag, before, after, fn in self.rules:
            if node in node.parent.select(tag):
                return (
                    before.format(**node.attrs)
                    + fn("".join([self._translate(child) for child in node.children]))
                    + after.format(**node.attrs)
                )
        else:
            if self.verbose:
                s = str(node)
                if len(s) < 100:
                    print(f"Ignoring {s}")
                else:
                    print(f"Ignoring {s[:50]} ... {s[-10:]}")

            return "".join([self._translate(child) for child in node.children])
