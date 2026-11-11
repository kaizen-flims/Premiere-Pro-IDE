#!/usr/bin/env python3
"""Apply the Podium Air 2.0.0 branding overlay to the pinned Android source."""
from pathlib import Path
import re
import shutil
import sys

project = Path(sys.argv[1]).resolve()
branding = Path(sys.argv[2]).resolve()

settings = project / "settings.gradle.kts"
settings.write_text("""pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
        maven("https://jitpack.io")
    }
}
rootProject.name = "Podium Air Android"
include(":shared", ":sharedUi", ":app")
""", encoding="utf-8")

root_gradle = project / "build.gradle.kts"
data = root_gradle.read_text(encoding="utf-8")
for old, new in [
    ('extra["bitchordVersionCode"] = 39', 'extra["podiumVersionCode"] = 4'),
    ('extra["bitchordVersionName"] = "1.9.1"', 'extra["podiumVersionName"] = "2.0.0"'),
    ('extra["bitchordBetaSuffix"] = ""', 'extra["podiumBetaSuffix"] = ""'),
]:
    if old not in data:
        raise SystemExit(f"Expected version setting not found: {old}")
    data = data.replace(old, new)
root_gradle.write_text(data, encoding="utf-8")

app_gradle = project / "app/build.gradle.kts"
data = app_gradle.read_text(encoding="utf-8")
for old, new in [
    ('rootProject.extra["bitchordBetaSuffix"]', 'rootProject.extra["podiumBetaSuffix"]'),
    ('rootProject.extra["bitchordVersionCode"]', 'rootProject.extra["podiumVersionCode"]'),
    ('rootProject.extra["bitchordVersionName"]', 'rootProject.extra["podiumVersionName"]'),
    ('applicationId = "com.music.bitchord"', 'applicationId = "com.podium.air"'),
    ('applicationId = "com.dev.bitchord"', 'applicationId = "com.dev.podium.air"'),
]:
    if old not in data:
        raise SystemExit(f"Expected app Gradle setting not found: {old}")
    data = data.replace(old, new)

# The updater asset prefix is a build-config string. Match the declaration
# structurally so formatting/escaping changes upstream cannot break branding.
data, prefix_count = re.subn(
    r'(?m)^\s*buildConfigField\("String",\s*"UPDATE_APK_PREFIX",.*\)$',
    lambda _: r'        buildConfigField("String", "UPDATE_APK_PREFIX", "\"Podium-Air-\"")',
    data,
)
if prefix_count != 1:
    raise SystemExit(f"Expected exactly one UPDATE_APK_PREFIX declaration, found {prefix_count}")
app_gradle.write_text(data, encoding="utf-8")

# Replace brand mentions in XML text nodes only. Avoid rewriting markup,
# attributes, or whitespace around tags. Keep Music/BitChord as the existing
# public storage folder so local files and downloads remain in place.
import xml.etree.ElementTree as ET

for base in [project / "app/src/main/res", project / "sharedUi/src/commonMain/composeResources"]:
    if not base.exists():
        continue
    for xml in base.glob("values*/strings.xml"):
        data = xml.read_text(encoding="utf-8")
        # Preserve the existing public storage-folder name only. Do not skip
        # the entire strings.xml file: it also contains app_name, which must
        # become Podium Air for Android's installer and launcher labels.
        storage_pattern = re.compile(
            r'(<string\s+name="saved_to_bitchord_folder"[^>]*>)(.*?)(</string>)',
            re.DOTALL,
        )
        storage_match = storage_pattern.search(data)
        storage_text = storage_match.group(2) if storage_match else None
        if storage_match:
            data = storage_pattern.sub(r"\1__PODIUM_STORAGE_LABEL_PRESERVED__\3", data, count=1)
        data = re.sub(
            r'(?<=>)([^<]*BitChord[^<]*)(?=<)',
            lambda m: m.group(1).replace("BitChord", "Podium Air"),
            data,
        )
        if storage_text is not None:
            data = data.replace("__PODIUM_STORAGE_LABEL_PRESERVED__", storage_text, 1)
        # Validate the transformed resource immediately so malformed XML is
        # caught here with its exact file path, before Gradle resource tasks.
        try:
            ET.fromstring(data)
        except ET.ParseError as exc:
            raise SystemExit(f"Invalid XML after branding in {xml}: {exc}")
        xml.write_text(data, encoding="utf-8")

replacements = {
    "app/src/main/java/com/music/bitchord/data/AppUpdateChecker.kt": [
        ("https://api.github.com/repos/kushagrasinghx/BitChord/releases/latest",
         "https://api.github.com/repos/kaizen-flims/Podium-Air/releases/latest"),
        ('"bitchord-${info.version}.apk"', '"podium-air-${info.version}.apk"'),
    ],
    "app/src/main/java/com/music/bitchord/BitChordApplication.kt": [
        ("BitChord/${BuildConfig.VERSION_NAME} (Android; +https://github.com/kushagrasinghx/BitChord)",
         "Podium Air/${BuildConfig.VERSION_NAME} (Android; +https://github.com/kaizen-flims/Podium-Air)"),
    ],
    "app/src/main/java/com/music/bitchord/data/discord/DiscordRPC.kt": [
        ("https://github.com/kushagrasinghx/BitChord", "https://github.com/kaizen-flims/Podium-Air"),
    ],
    "app/src/main/java/com/music/bitchord/data/scrobbling/LastFM.kt": [
        ("BitChord (https://github.com/kushagrasinghx/BitChord)",
         "Podium Air (https://github.com/kaizen-flims/Podium-Air)"),
    ],
    "app/src/main/java/com/music/bitchord/ui/screens/SettingsSheet.kt": [
        ("https://github.com/kushagrasinghx/BitChord", "https://github.com/kaizen-flims/Podium-Air"),
    ],
}
for rel, pairs in replacements.items():
    path = project / rel
    data = path.read_text(encoding="utf-8")
    for old, new in pairs:
        if old not in data:
            raise SystemExit(f"Expected branding target not found in {rel}: {old}")
        data = data.replace(old, new)
    path.write_text(data, encoding="utf-8")

legacy = branding / "legacy_icon.png"
if not legacy.is_file():
    raise SystemExit("Missing branding/legacy_icon.png. Upload the Legacy icon before running this workflow.")
icon_dir = project / "app/src/main/res/drawable-nodpi"
icon_dir.mkdir(parents=True, exist_ok=True)
shutil.copy2(legacy, icon_dir / "legacy_icon.png")

manifest = project / "app/src/main/AndroidManifest.xml"
data = manifest.read_text(encoding="utf-8")
data = data.replace('@mipmap/ic_launcher_round', '@drawable/legacy_icon')
data = data.replace('@mipmap/ic_launcher', '@drawable/legacy_icon')
# The home-screen launcher entry is an activity-alias and carries its own
# icon attribute. Point that alias at the same Legacy icon as the application
# itself, otherwise the launcher keeps showing BitChord's old adaptive icon.
alias_pattern = re.compile(
    r'(<activity-alias\s+android:name="\.LauncherDefault".*?</activity-alias>)',
    re.DOTALL,
)
data, alias_count = alias_pattern.subn(
    lambda m: m.group(1).replace('@mipmap/ic_launcher', '@drawable/legacy_icon'),
    data,
)
if alias_count != 1:
    raise SystemExit(f"Expected exactly one LauncherDefault alias, found {alias_count}")
manifest.write_text(data, encoding="utf-8")

app_icon = project / "app/src/main/java/com/music/bitchord/AppIcon.kt"
data = app_icon.read_text(encoding="utf-8")
old = 'Default("LauncherDefault", R.mipmap.ic_launcher, R.string.app_icon_default)'
new = 'Default("LauncherDefault", R.drawable.legacy_icon, R.string.app_icon_default, R.drawable.legacy_icon)'
if old not in data:
    raise SystemExit("Default launcher icon entry not found.")
app_icon.write_text(data.replace(old, new), encoding="utf-8")

shutil.copy2(branding / "PodiumAir black.svg", project / "app/src/main/assets/Logo.svg")
white_svg = (branding / "PodiumAir white.svg").read_text(encoding="utf-8")
shutil.copy2(branding / "PodiumAir white.svg", project / "app/src/main/assets/LogoTransparent.svg")
path_match = re.search(r'<path[^>]*\bd="([^"]+)"', white_svg)
if not path_match:
    raise SystemExit("Could not read path data from the supplied white SVG.")
path_data = path_match.group(1)
notification = project / "app/src/main/res/drawable/ic_notification_logo.xml"
notification.write_text(f'''<!-- Podium Air notification mark. Android renders this as a white silhouette. -->
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp"
    android:height="24dp"
    android:viewportWidth="24"
    android:viewportHeight="24">
    <group android:scaleX="0.0234375" android:scaleY="0.0234375">
        <path android:fillColor="#FFFFFFFF" android:pathData="{path_data}"/>
    </group>
</vector>
''', encoding="utf-8")

assert 'applicationId = "com.podium.air"' in app_gradle.read_text(encoding="utf-8")
assert 'extra["podiumVersionCode"] = 4' in root_gradle.read_text(encoding="utf-8")
assert 'extra["podiumVersionName"] = "2.0.0"' in root_gradle.read_text(encoding="utf-8")
assert (icon_dir / "legacy_icon.png").is_file()
assert "kaizen-flims/Podium-Air/releases/latest" in (project / "app/src/main/java/com/music/bitchord/data/AppUpdateChecker.kt").read_text(encoding="utf-8")
print("Podium Air Android branding applied and verified.")
