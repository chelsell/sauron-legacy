#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

if (( $# == 1 )) && [[ "${1}" == "--help" ]]; then
	echo "Usage: ${0}"
	echo "Dumps the schema to schema.sql."
	echo "Requires environment vars VALAR_USER and VALAR_PASSWORD"
	exit 0
fi

valar_port="3306"
db_name="valar"
valar_user_="${VALAR_USER}"
valar_password_="${VALAR_PASSWORD}"

if (( $# > 0 )); then
	(>&2 echo "Usage: ${0}")
	exit 1
fi

mysqldump \
  --skip-add-drop-table \
  --single-transaction \
  --host=127.0.0.1 \
  --port="${valar_port}" \
  --user="${valar_user_}" \
  --password="${valar_password_}" \
  --no-data \
  "${db_name}" \
  > "schema-${db_name}.sql"

sed -r -i -e 's/AUTO_INCREMENT=[0-9]+ //g' "schema-${db_name}.sql"
