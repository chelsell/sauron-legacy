#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

if (( $# == 1 )) && [[ "${1}" == "--help" ]]; then
	echo "Usage: ${0}"
	echo "Writes an ERD of the schema in graphml to erd.graphml."
	echo "Requires environment vars VALAR_USER and VALAR_PASSWORD"
	exit 0
fi

if (( $# > 0 )); then
	(>&2 echo "Usage: ${0}")
	exit 1
fi

if [[ ! -e "{$HOME}/.groovy" ]]; then
  mkdir "{$HOME}/.groovy"
fi
wget https://dev.mysql.com/get/Downloads/Connector-J/mysql-connector-java-8.0.23.zip
unzip mysql-connector-java-8.0.23.zip -d "{$HOME}/.groovy"

groovy erd.groovy > erd.graphml
