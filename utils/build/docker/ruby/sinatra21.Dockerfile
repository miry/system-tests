FROM ghcr.io/datadog/dd-trace-rb/ruby:3.1.1-dd

RUN mkdir -p /app
WORKDIR /app

RUN gem install ddtrace # Install base revision to improve dependency caching during development
RUN gem install sinatra -v '~> 2.1.0'
RUN gem install rack-contrib
RUN gem install pry -v '0.14.1'
RUN gem install puma -v '5.6.1'
RUN gem install libdatadog -v '3.0.0.1.0'
RUN gem install nio4r -v '2.5.8'
RUN gem install mustermann -v '1.1.1'
RUN gem install rack -v '2.2.3'
RUN gem install tilt -v '2.0.10'

COPY utils/build/docker/ruby/sinatra21/ .

COPY utils/build/docker/ruby/install_ddtrace.sh binaries* /binaries/
RUN /binaries/install_ddtrace.sh

ENV DD_TRACE_HEADER_TAGS=user-agent

RUN echo "#!/bin/bash\nbundle exec puma -b tcp://0.0.0.0 -p 7777 -w 1" > app.sh
RUN chmod +x app.sh
CMD [ "./app.sh" ]
