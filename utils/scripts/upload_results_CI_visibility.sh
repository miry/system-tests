if [ "$#" -ne 3 ] ; then
  echo "Script execution requires 3 parameters: environment name (dev, prod), language (java,node...) and weblog variant name " 
  exit 1
fi
SYS_TEST_ENV=$1
SYS_TEST_LANG=$2
SYS_TEST_WEBLOG=$3

if test -f ".env"; then
    source .env
fi

export DD_CIVISIBILITY_LOGS_ENABLED='1'
export DD_CIVISIBILITY_AGENTLESS_ENABLED='1'
export DD_SITE=datadoghq.com

#Download tool
curl -L --fail "https://github.com/DataDog/datadog-ci/releases/latest/download/datadog-ci_linux-x64" --output "$(pwd)/datadog-ci" && chmod +x $(pwd)/datadog-ci
for folder in $(find . -name "logs*" -type d -maxdepth 1); do 
    ./datadog-ci junit upload --service ci-system-test-$SYS_TEST_LANG-$SYS_TEST_WEBLOG --env env-system-test-$SYS_TEST_ENV $folder/reportJunit.xml 
done




