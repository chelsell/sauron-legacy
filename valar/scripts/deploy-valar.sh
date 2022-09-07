#!/usr/bin/env bash

(cd /var/dev/valar-backend/ && sbt clean && sbt assembly)
mv /var/dev/valar-backend/target/valar-backend.jar /var/stage/valar-backend.jar
