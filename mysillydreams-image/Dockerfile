# MySillyDreams — Custom image overlay on top of OpenProject's slim build
#
# Build from repo root:
#   docker build --target msd-slim -f mysillydreams-image/Dockerfile .
#
# CI (GitHub Actions self-hosted runner on mysillydreams-vm) runs this
# automatically on every push to main.

FROM openproject/openproject:17-slim AS msd-slim

USER root

# ── Static brand asset replacement ──────────────────────────────────────────
COPY mysillydreams-image/assets/logo_openproject.png           /app/public/assets/logo_openproject.png
COPY mysillydreams-image/assets/logo_openproject_narrow.svg    /app/public/assets/logo_openproject_narrow.svg
COPY mysillydreams-image/assets/logo_openproject_white_big.png /app/public/assets/logo_openproject_white_big.png
COPY mysillydreams-image/assets/icon_logo.svg                  /app/public/assets/icon_logo.svg
COPY mysillydreams-image/assets/icon_logo_white.svg            /app/public/assets/icon_logo_white.svg
COPY mysillydreams-image/assets/favicon.ico                    /app/public/favicon.ico

# ── Locale string rebrand ────────────────────────────────────────────────────
# Belt-and-suspenders: source files are also patched in the repo directly,
# but this find+sed covers every locale file (incl. modules & Crowdin translations)
# in case the base image is updated with new strings.
RUN find /app/config/locales /app/modules -name "*.yml" -exec \
    sed -i \
      -e 's/OpenProject/MySillyDreams/g' \
      -e 's|https://www\.openproject\.org|https://mysillydreams.com|g' \
      -e 's|https://community\.openproject\.org|https://mysillydreams.com/community|g' \
    {} \;

# ── Fix ownership ────────────────────────────────────────────────────────────
RUN chown app:app \
    /app/public/assets/logo_openproject.png \
    /app/public/assets/logo_openproject_narrow.svg \
    /app/public/assets/logo_openproject_white_big.png \
    /app/public/assets/icon_logo.svg \
    /app/public/assets/icon_logo_white.svg \
    /app/public/favicon.ico

USER app
