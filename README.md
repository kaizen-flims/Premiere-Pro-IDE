# Podium Air Android Build Station

This repository builds the Android phone app only. It fetches the pinned BitChord v1.9.1 upstream source, copies only the Android app and its required shared modules, applies the Podium Air branding overlay, and builds a signed universal APK.

## Before the first build

1. Upload the **Legacy launcher icon** to `branding/legacy_icon.png` (PNG, square, preferably 1024×1024). Do not rename it.
2. Add the four signing secrets listed below under **Settings → Secrets and variables → Actions**. They must contain the same release keystore and credentials used to sign the currently released Podium Air APK. Never commit the keystore or passwords.
3. Open **Actions → Build Podium Air Android → Run workflow**. The workflow is manual only; uploading files does not trigger it.

## Required Actions secrets

- `PODIUM_RELEASE_KEYSTORE_BASE64`: Base64-encoded existing Podium Air release keystore.
- `PODIUM_RELEASE_STORE_PASSWORD`
- `PODIUM_RELEASE_KEY_ALIAS`
- `PODIUM_RELEASE_KEY_PASSWORD`

The workflow intentionally stops if the release-signing secrets are missing. A debug or unsigned APK would not be a valid update for existing Podium Air installations.

## Output

Download the `Podium-Air-v2.0.0` artifact from the completed workflow run. It contains `Podium-Air-v2.0.0.apk`, the universal APK. This workflow does not create a GitHub Release and does not touch the main Podium Air repository.

## Branding assets

- `branding/legacy_icon.png`: launcher icon, uploaded manually by the repository owner.
- `branding/PodiumAir black.svg`: black in-app mark.
- `branding/PodiumAir white.svg`: white in-app mark.

The Android application ID is `com.podium.air`; its internal Kotlin namespace remains `com.music.bitchord` to avoid an unnecessary package-wide source refactor. Version name: `2.0.0`. Version code: `4`.

## Upstream and licensing

The Android application is based on Kushagra Singh's BitChord v1.9.1, licensed under GPL-3.0. Upstream source and attribution are retained during the build. See [UPSTREAM_NOTICE.md](UPSTREAM_NOTICE.md).
