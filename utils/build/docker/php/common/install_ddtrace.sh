#!/bin/bash

set -eu

echo "Loading install script"
curl -Lf -o /tmp/datadog-setup.php \
  https://github.com/DataDog/dd-trace-php/releases/download/0.70.0/datadog-setup.php

cd /binaries

export DD_APPSEC_ENABLED=0
PHP_INI_SCAN_DIR=/etc/php/ php /tmp/datadog-setup.php \
  --enable-appsec \
  --enable-profiling \
  --php-bin all

php -r 'echo phpversion("ddtrace");' > \
  ./SYSTEM_TESTS_LIBRARY_VERSION

php -r 'echo phpversion("ddappsec");' > \
  ./SYSTEM_TESTS_PHP_APPSEC_VERSION

# What are these files for? todo: use profiling version
php -r 'echo phpversion("datadog-profiling");' > \
  ./SYSTEM_TESTS_PHP_PROFILING_VERSION

touch SYSTEM_TESTS_LIBDDWAF_VERSION

find /opt -name ddappsec-helper -exec ln -s '{}' /usr/local/bin/ \;
mkdir -p /etc/dd-appsec
find /opt -name recommended.json -exec ln -s '{}' /etc/dd-appsec/ \;

# TODO: verify that the latest installer is cleaning all these up
#rm -rf /tmp/{dd-library-php-setup.php,dd-library,dd-appsec}
