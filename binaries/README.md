This folder will contains binaries to be tested

Debugging the RC issue:

Add one of these to a file called `ruby-load-from-bundle-add` in this same diretory (`binaries/`). Add only the `gem` line, not the comment:

# good (working revision)
gem 'ddtrace', git: 'https://github.com/Datadog/dd-trace-rb', ref: 'c06a389727542b9f6ebaafb1ecb049499b00925b', require: 'ddtrace/auto_instrument'
# bad (issue is introduced here)
gem 'ddtrace', git: 'https://github.com/Datadog/dd-trace-rb', ref: '8f596b56f4f46f51a2ebea88d430f5ee0e6dcaf2', require: 'ddtrace/auto_instrument'

The main issue I see so far is this error:
```
E, [2023-07-27T23:25:31.419856 #16] ERROR -- : remote worker client sync error: no valid content for target at path 'datadog/2/ASM/ASM-base/config' location: app.rb:387:in `block (2 levels) in sync'. skipping sync
```
Which means RC did not consume data correctly. Subsequent RC invocations by the RC worker do not fix the issue either.

I've been running my tests like this:
`./build.sh ruby --weblog-variant sinatra21 && ./run.sh -S APPSEC_REQUEST_BLOCKING; cat logs_appsec_request_blocking/docker/weblog/stdout.log`

Your log outputs are in the directory: `logs_appsec_request_blocking/docker/weblog` (after tests finish running)