from __future__ import annotations

import re, os, json
from pathlib import Path
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup

from pprint import pprint

from aqt import gui_hooks, editor, mw

"""
addon_path = mw.addonManager.addon_from_module(__name__)
resources_path = Path(mw.addonManager.addonsFolder()) / addon_path / "resources"
"""

tense_mapping: dict[str, str] = {
    "Indicatif Présent": "Présent",
    "Indicatif Imparfait": "Imparfait",
    "Indicatif Futur": "Futur Simple",
    "Indicatif Passé simple": "Passé Simple",
    "Subjonctif Présent": "Subjonctif",
    "Subjonctif Imparfait": "Imparfait du Subjonctif",
    "Conditionnel Présent": "Conditionnel",
    "Impératif Présent": "Impératif",

    "Participe Présent": "Participe Présent",
    "Participe Passé": "Participe Passé",
}

@dataclass
class Conjugation:
    tenses: dict[str, list[str]]
    exact: bool

def get_conjugation(verb: str):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    }

    response = requests.get("https://conjugator.reverso.net/conjugation-french-verb-"+verb+".html", headers=headers)
    if not response.ok:
        return None
    
    soup = BeautifulSoup(response.text, "html.parser")

    all_conjugated: dict[str, list[str]] = {}
    for box in soup.find_all(class_="blue-box-wrap"):
        title: str = box.get("mobile-title")
        if title not in tense_mapping: continue
        title = tense_mapping[title]
        listing = box.find(class_="wrap-verbs-listing")

        one_conjugated: list[str] = []
        if next(listing.children, None) is None:
            one_conjugated.append("N/A")
        else:
            for i, list_item in enumerate(listing.find_all("li")):
                if list_item.get("v") == "2":
                    break
                
                if "Participe" in title:
                    one_conjugated.append(list_item.find(class_="verbtxt").get_text())
                    break
                
                text = list_item.get_text()
                if "Impératif" in title:
                    text = "(" + ["tu", "nous", "vous"][i] + ") " + text

                one_conjugated.append(text.replace("il/elle ", "il ").replace("ils/elles ", "ils ").replace("que ", "").replace("qu'", ""))

        all_conjugated[title] = one_conjugated

    return Conjugation(all_conjugated, not soup.find(class_="approximate-note"))

def on_button(ed: editor.Editor):
    note_type = ed.note_type()
    note = ed.note
    if note_type["name"] == "FR::Verb":
        conjugations = get_conjugation(note["Infinitif"])
        pprint(conjugations)
        if conjugations.exact:
            for tense, forms in conjugations.tenses.items():     
                note[tense] = "<br>".join(forms)
        else:
            pass

    ed.loadNote()

def add_button(buttons, ed: editor.Editor):
    button = ed.addButton(
        icon = None,
        cmd = "fci-conjugate",
        func = on_button,
        label = "Conjugate"
    )
    buttons.append(button)
    print("BUTTON ADDED")
    return buttons

gui_hooks.editor_did_init_buttons.append(add_button)