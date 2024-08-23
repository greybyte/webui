#!/bin/bash

set -e

cd "$(dirname "$0")/.."

echo ''
echo 'UNIT TESTS'
echo ''

python3 -m pytest

function failure() {
  echo ''
  echo '### FAILED ###'
  echo ''
  pkill -f ansibleguy_webui
  exit 1
}

echo ''
echo 'INTEGRATION TESTS WEB-UI'
echo ''

if pgrep -f 'ansibleguy_webui'
then
  echo 'An instance of Ansible-WebUI is already running! Stop it first (pkill -f ansibleguy_webui)'
  exit 1
fi


echo 'Starting AnsibleGuy-WebUI..'
export AW_ENV='dev'
# shellcheck disable=SC2155
export AW_DB="/tmp/$(date +%s).aw.db"
# shellcheck disable=SC2155
export AW_PATH_PLAY="$(pwd)/test"
export AW_ADMIN='tester'
export AW_ADMIN_PWD='someSecret!Pwd'
python3 src/ansibleguy_webui/ >/dev/null 2>/dev/null &
echo ''
sleep 5

set +e
if ! python3 test/integration/webui/main.py
then
  failure
fi

sleep 1

echo ''
echo 'INTEGRATION TESTS API'
echo ''

echo 'Create API key'
api_key="$(python3 src/ansibleguy_webui/cli.py -a api-key.create -p "$AW_ADMIN" | grep 'Key=' | cut -d '=' -f2)"
export AW_API_KEY="$api_key"
sleep 1

if ! python3 test/integration/api/main.py
then
  failure
fi

sleep 1
pkill -f 'ansibleguy_webui'

echo ''
echo 'INTEGRATION TESTS SAML'
echo ''

sleep 5

echo 'Starting AnsibleGuy-WebUI with SAML enabled..'
# shellcheck disable=SC2155
export AW_DB="/tmp/$(date +%s).aw.db"
# shellcheck disable=SC2155
export AW_CONFIG="$(pwd)/test/integration/auth/saml.yml"
python3 src/ansibleguy_webui/ >/dev/null 2>/dev/null &
echo ''
sleep 5

set +e
if ! python3 test/integration/auth/saml.py
then
  failure
fi

sleep 1
export AW_CONFIG=''
pkill -f 'ansibleguy_webui'

echo ''
echo 'TESTING TO CLI TOOLS'
echo ''

REPO_BASE="$(pwd)"
cd /tmp
export AW_DB="${REPO_BASE}/src/ansibleguy_webui/aw.dev.db"
python3 "${REPO_BASE}/src/ansibleguy_webui/cli.py" --version
python3 "${REPO_BASE}/src/ansibleguy_webui/manage.py"
cd "$REPO_BASE"

echo ''
echo 'TESTING TO INITIALIZE AW-DB'
echo ''

# shellcheck disable=SC2155
TMP_DIR="/tmp/aw_$(date +%s)"
mkdir -p "$TMP_DIR"
cp -r ./* "$TMP_DIR"
cd "$TMP_DIR"
rm -rf ./src/ansibleguy_webui/aw/migrations/*
export AW_DB="${TMP_DIR}/aw.db"
timeout 10 python3 src/ansibleguy_webui
ec="$?"
if [[ "$ec" != "124" ]]
then
  exit 1
fi

echo ''
echo '### FINISHED ###'
echo ''
