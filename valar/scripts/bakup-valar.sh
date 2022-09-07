#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

if (( $# == 1 )) && [[ "${1}" == "--help" ]]; then
	echo "Usage: ${0} [<path=/bak/mariadb/valar/>]"
	echo "Exports all the data in Valar as one gzipped sql file per table."
	echo "Requires environment vars VALAR_USER and VALAR_PASSWORD"
	exit 0
fi

# Modify this
loc="/bak/mariadb/valar/nightly"
valar_port="3306"
db_name="valar"
valar_user_="${VALAR_USER}"
valar_password_="${VALAR_PASSWORD}"

if (( $# > 0 )); then
	(>&2 echo "Usage: ${0}")
	exit 1
fi

for t in $(mysql -NBA -u "${valar_user_}" --password="${valar_password_}" -D "${db_name}" -e 'show tables'); do
	echo "Backing up $t..."
	# 2147483648 is the max
	# output blobs as hex, then gzip. It's a bit weird but is more compressed and makes files that are easier to view.
	mysqldump \
	--single-transaction \
	--hex-blob \
	--max_allowed_packet=2147483648 \
	--port="${valar_port}" \
	--user="${valar_user_}" \
	--password="${valar_password_}" \
	"${db_name}" \
	"${t}" \
	| gzip > "${loc}/${t}.sql.gz"
done

echo "Backed up to ${loc}"
