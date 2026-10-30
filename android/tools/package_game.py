#!/usr/bin/env python3
"""Merge the locally built launcher/server into a user-supplied decoded game.

Run the upstream lunar-scripts patcher on the decoded directory first. This tool
does not download or distribute game files. It never edits the source APK.
"""
import argparse
import copy
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import xml.etree.ElementTree as ET
import zipfile

import build_info
import command
import region

NS = "http://schemas.android.com/apk/res/android"
ET.register_namespace("android", NS)
def attr(name): return "{" + NS + "}" + name
def run(*args): subprocess.run(command.command(*args), check=True)

def patch_local_reachability(game):
    """Let this local-only 3.7.1 client load assets with all radios disabled.

    Unity's reachability getter otherwise returns NotReachable in airplane mode,
    and Octo rejects a successful loopback download. Return LAN reachability.
    Both releases compile the same IL2CPP wrapper for
    UnityEngine.Application::get_internetReachability(), and only that wrapper
    materialises the address of its name string in the library. Finding the
    string first keeps this working for 日服 and 全球服 alike, where the code
    sits at different addresses, and refuses a binary it does not recognise
    instead of writing an offset speculatively.
    """
    path=game/"lib/arm64-v8a/libil2cpp.so"
    data=bytearray(path.read_bytes())
    if data[:6] != b"\x7fELF\x02\x01" or struct.unpack_from("<H",data,18)[0] != 183:
        raise RuntimeError("Expected the Android ARM64 game library")
    offset=reachability_wrapper(data)
    if data[offset:offset+8] == PATCHED_PROLOGUE:
        print("Local asset reachability already enabled")
        return
    data[offset:offset+8]=PATCHED_PROLOGUE
    path.write_bytes(data)
    print("Local asset reachability enabled (works with radios disabled)")

REACHABILITY_NAME=b"UnityEngine.Application::get_internetReachability()"
ORIGINAL_PROLOGUE=bytes.fromhex("f30f1ef8fd7b01a9")  # str x19, [sp, #-16]!; stp x29, x30, [sp, #16]
PATCHED_PROLOGUE=bytes.fromhex("40008052c0035fd6")   # mov w0, #2; ret

def reachability_wrapper(data):
    """The file offset of the IL2CPP wrapper for internetReachability.

    ARM64 lays this library out with a zero-based executable segment, so a
    virtual address is its file offset (the patchers rely on that too). The
    wrapper is the only code that computes the address of the property's name
    string, as adrp xD, <page>; add xD, xD, #<offset>.
    """
    name=data.find(REACHABILITY_NAME)
    if name < 0: raise RuntimeError("Unsupported game binary: no internetReachability name")
    sites=_references(data,name)
    if len(sites) != 1:
        raise RuntimeError(f"Unsupported game binary: {len(sites)} internetReachability references")
    # The wrapper starts at the prologue that saves x19 and the frame pointer,
    # at most a few instructions before the address it computes.
    # Idempotent: a wrapper that is already patched keeps the original body
    # after the replacement, so both forms are recognised.
    for start in range(sites[0]-8, sites[0]-40, -4):
        if data[start:start+8] not in (ORIGINAL_PROLOGUE, PATCHED_PROLOGUE): continue
        frame=int.from_bytes(data[start+8:start+12],"little")
        # add x29, sp, #imm: the frame the earlier instructions set up.
        if frame & 0xFFC00000 == 0x91000000 and (frame >> 5) & 0x1F == 31 and frame & 0x1F == 29:
            return start
    raise RuntimeError("Unsupported game binary: no reachability wrapper prologue")

def _references(data, target):
    """The offsets of adrp/add pairs that compute target.

    page + imm12 == target with imm12 below 4096, so page is target's own 4 KB
    page and imm12 is known in advance. The two encoding bytes that imm12 fixes
    are rare enough to scan for directly, which keeps this to a couple of
    seconds over a 127 MB library.
    """
    delta=target & 0xFFF
    page=target & ~0xFFF
    # add xD, xD, #imm12 is 0x91000000 | imm12<<10 | Rn<<5 | Rd, so the top
    # two bytes are fixed by imm12: [imm12>>6, 0x91].
    high=bytes(((delta >> 6) & 0xFF, 0x91))
    middle=(delta & 0x3F) << 2  # the six imm12 bits that land in the next byte
    sites=[]
    at=data.find(high)
    while at >= 0:
        add_at=at-2
        if add_at >= 0 and add_at % 4 == 0 and data[add_at+1] & 0xFC == middle:
            add=int.from_bytes(data[add_at:add_at+4],"little")
            if ((add >> 10) & 0xFFF) == delta and (add >> 5) & 0x1F == add & 0x1F:
                rd=add & 0x1F
                for back in (1, 2, 3):
                    if add_at < back*4: continue
                    adrp=int.from_bytes(data[add_at-back*4:add_at-back*4+4],"little")
                    if adrp & 0x9F000000 != 0x90000000 or adrp & 0x1F != rd: continue
                    imm=(((adrp >> 5) & 0x7FFFF) << 2) | ((adrp >> 29) & 0x3)
                    if imm & (1 << 20): imm -= 1 << 21
                    # The adrp's own PC decides the page it computes.
                    if (((add_at-back*4) & ~0xFFF) + (imm << 12)) & 0xFFFFFFFFFFFFFFFF == page:
                        sites.append(add_at)
                        break
        at=data.find(high,at+1)
    return sites


def build_tools(sdk):
    """The SDK build-tools folder to sign with: 36.0.0, else the newest 36.x.

    Android Studio now installs 36.1.0 and later alongside or instead of
    36.0.0, and zipalign/apksigner behave the same across the series.
    """
    root=sdk/"build-tools"
    preferred=root/"36.0.0"
    if preferred.is_dir(): return preferred
    candidates=[]
    if root.is_dir():
        for path in root.iterdir():
            parts=path.name.split(".")
            if path.is_dir() and parts[0].isdigit() and int(parts[0])>=36:
                candidates.append((tuple(int(x) if x.isdigit() else 0 for x in parts),path))
    if not candidates:
        raise RuntimeError(f"Install Android SDK build-tools 36 or newer; looked in {root}")
    return max(candidates)[1]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--decoded-dir",type=Path,required=True)
    p.add_argument("--companion-apk",type=Path,required=True)
    p.add_argument("--game-apk",type=Path,required=True,help="The original game APK (its manifest and dex count go into build.json)")
    p.add_argument("--sdk",type=Path,default=Path(os.environ.get("ANDROID_HOME",str(Path.home()/"Library/Android/sdk"))))
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--keystore",type=Path,required=True)
    p.add_argument("--key-alias",default="lunar-local",help="Keystore alias (region key auto-select passes nier/androiddebugkey)")
    p.add_argument("--key-pass",default="android",help="Keystore/key password (region key auto-select passes lunar-jp/android)")
    p.add_argument("--port-offset",type=int,default=0,help="The offset the game was patched with (ports 8003/8080/3000)")
    p.add_argument("--region",choices=sorted(region.REGIONS),help="Game release; detected from the decoded manifest when omitted")
    args=p.parse_args()
    root=Path(__file__).resolve().parents[2]
    game=args.decoded_dir.resolve();output=args.output.resolve();output.parent.mkdir(parents=True,exist_ok=True)
    manifest=game/"AndroidManifest.xml";tree=ET.parse(manifest);doc=tree.getroot();app=doc.find("application")
    if app is None: raise RuntimeError("Game manifest has no application")
    package=doc.attrib["package"]
    # The release decides which library layout to look for and what build.json records.
    release=region.resolve(args.region,region.region_for_package(package)) if args.region else \
        region.region_for_package(package)
    if release is None: raise RuntimeError(f"Unknown game release for package {package}")
    patch_local_reachability(game)
    old=app.find("meta-data[@"+attr("name")+"='org.veritr1x.bunker.GAME_ACTIVITY']")
    original=old.get(attr("value")) if old is not None else None
    for activity in list(app.findall("activity")):
        if activity.get(attr("name"))=="org.veritr1x.bunker.MainActivity":
            app.remove(activity);continue
        for intent in list(activity.findall("intent-filter")):
            if any(x.get(attr("name"))=="android.intent.category.LAUNCHER" for x in intent.findall("category")):
                original=activity.get(attr("name"));activity.remove(intent)
    if not original: raise RuntimeError("Cannot identify the original game launcher")
    if original.startswith("."): original=package+original
    elif "." not in original: original=package+"."+original
    for entry in list(app):
        if entry.get(attr("name")) in ["org.veritr1x.bunker.GAME_ACTIVITY","org.veritr1x.bunker.PORT_OFFSET","org.veritr1x.bunker.REGION","org.veritr1x.bunker.ServerService","org.veritr1x.bunker.ToolsActivity"]:app.remove(entry)
    ET.SubElement(app,"meta-data",{attr("name"):"org.veritr1x.bunker.GAME_ACTIVITY",attr("value"):original})
    # The launcher and server read the ports the game was built for.
    ET.SubElement(app,"meta-data",{attr("name"):"org.veritr1x.bunker.PORT_OFFSET",attr("value"):str(args.port_offset)})
    # Which release this build is, so an update never crosses regions.
    ET.SubElement(app,"meta-data",{attr("name"):"org.veritr1x.bunker.REGION",attr("value"):release})
    app.set(attr("usesCleartextTraffic"),"true");app.set(attr("appCategory"),"game");app.set(attr("allowBackup"),"false");app.set(attr("extractNativeLibs"),"true")
    # The original Unity libraries use 4 KB ELF pages. Request Android's
    # compatibility loader explicitly, including after an APK update.
    app.set(attr("pageSizeCompat"),"enabled")
    # Keep the game's own name ("NieR"), as the iOS build does.
    companion=ET.parse(root/"android/app/src/main/AndroidManifest.xml").getroot()
    permissions={x.get(attr("name")) for x in doc.findall("uses-permission")}
    for permission in companion.findall("uses-permission"):
        if permission.get(attr("name")) not in permissions:doc.insert(0,copy.deepcopy(permission))
    for name in ["activity","service","provider"]:
        for source in companion.findall("application/"+name):
            element=copy.deepcopy(source)
            element.set(attr("name"),"org.veritr1x.bunker"+element.get(attr("name")))
            if name=="activity":element.set(attr("theme"),"@android:style/Theme.Material.Light.NoActionBar")
            # Authorities are unique per device: use the game's, not the standalone companion's.
            if name=="provider":element.set(attr("authorities"),doc.get("package")+".lunar_loopback")
            app.append(element)
    ET.indent(tree,space="    ");tree.write(manifest,encoding="utf-8",xml_declaration=True)
    # The wrapper uses Android 9+ file APIs. Preserve the game's target SDK to
    # avoid changing Unity's behavior; raise only its minimum supported version.
    yml=game/"apktool.yml";yml.write_text(re.sub(r"minSdkVersion: \d+","minSdkVersion: 28",yml.read_text()))
    with zipfile.ZipFile(args.companion_apk) as source:
        for name in source.namelist():
            if name.startswith(("assets/lunar/", "assets/chaquopy/", "lib/arm64-v8a/")):
                dest=game/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(source.read(name))
    notices=game/"assets/lunar";notices.mkdir(parents=True,exist_ok=True)
    shutil.copy2(root/"LICENSE",notices/"LUNAR_TEAR_LICENSE.txt")
    # What an update in place needs (build_info.py): the game's own manifest and dex count.
    with zipfile.ZipFile(args.game_apk) as game_apk,zipfile.ZipFile(args.companion_apk) as source:
        game_dex=sum(1 for n in game_apk.namelist() if re.fullmatch(r"classes\d*\.dex",n))
        (notices/"build.json").write_text(json.dumps(build_info.describe(source,game_dex,args.port_offset,release),indent=1))
        (notices/"game-manifest.xml").write_bytes(game_apk.read("AndroidManifest.xml"))
    unsigned=output.with_suffix(".unsigned.apk");merged=output.with_suffix(".merged.apk")
    run("apktool","b",game,"-o",unsigned)
    shutil.copyfile(unsigned,merged)
    with zipfile.ZipFile(merged,"a") as target,zipfile.ZipFile(args.companion_apk) as source:
        dex=[n for n in target.namelist() if re.fullmatch(r"classes\d*\.dex",n)]
        index=max(int(re.search(r"\d+",n).group()) if re.search(r"\d+",n) else 1 for n in dex)+1
        for name in sorted(n for n in source.namelist() if re.fullmatch(r"classes\d*\.dex",n)):
            target.writestr("classes%d.dex"%index,source.read(name),compress_type=zipfile.ZIP_DEFLATED);index+=1
    tools=build_tools(args.sdk)
    run(tools/"zipalign","-P","16","-f","4",merged,output)
    if not args.keystore.exists():
        args.keystore.parent.mkdir(parents=True,exist_ok=True)
        run("keytool","-genkeypair","-keystore",args.keystore,"-alias",args.key_alias,"-storepass",args.key_pass,"-keypass",args.key_pass,"-keyalg","RSA","-keysize","2048","-validity","10000","-dname","CN=Lunar Tear Local Build")
        os.chmod(args.keystore,0o600)
    run(tools/"apksigner","sign","--ks",args.keystore,"--ks-key-alias",args.key_alias,"--ks-pass","pass:"+args.key_pass,"--key-pass","pass:"+args.key_pass,output)
    run(tools/"apksigner","verify","--verbose",output)
    run(tools/"zipalign","-c","-P","16","4",output)
    unsigned.unlink();merged.unlink()
    print("Combined APK:",output)
    print("Original game activity:",original)

if __name__=="__main__":main()
