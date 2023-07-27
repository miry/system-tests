ENV.delete("DD_TRACE_HEADER_TAGS")#] = "user-agent"

require 'pry'
require 'sinatra'
require "net/http"
require "uri"
require 'json'

require 'ddtrace/auto_instrument'

require 'ddtrace'

module Datadog
  module AppSec
    module Contrib
      module Rack
        module Reactive
          # Dispatch data from a Rack request to the WAF context
          module Request
            # rubocop:disable Metrics/MethodLength
            def self.subscribe(op, waf_context)
              op.subscribe(*ADDRESSES) do |*values|
                Datadog.logger.debug { "reacted to #{ADDRESSES.inspect}: #{values.inspect}" }
                headers = values[0]
                headers_no_cookies = headers.dup.tap { |h| h.delete('cookie') }
                uri_raw = values[1]
                query = values[2]
                cookies = values[3]
                client_ip = values[4]
                request_method = values[5]

                waf_args = {
                  'server.request.cookies' => cookies,
                  'server.request.query' => query,
                  'server.request.uri.raw' => uri_raw,
                  'server.request.headers' => headers,
                  'server.request.headers.no_cookies' => headers_no_cookies,
                  'http.client_ip' => client_ip,
                  'server.request.method' => request_method,
                }

                waf_timeout = Datadog.configuration.appsec.waf_timeout
                result = waf_context.run(waf_args, waf_timeout)

                Datadog.logger.debug { "WAF ARGS: #{waf_args.inspect}" }
                Datadog.logger.debug { "WAF TIMEOUT: #{result.inspect}" } if result.timeout

                case result.status
                when :match
                  Datadog.logger.debug { "WAF: #{result.inspect}" }

                  block = result.actions.include?('block')

                  yield [result, block]

                  throw(:block, [result, true]) if block
                when :ok
                  Datadog.logger.debug { "WAF OK: #{result.inspect}" }
                when :invalid_call
                  Datadog.logger.debug { "WAF CALL ERROR: #{result.inspect}" }
                when :invalid_rule, :invalid_flow, :no_rule
                  Datadog.logger.debug { "WAF RULE ERROR: #{result.inspect}" }
                else
                  Datadog.logger.debug { "WAF UNKNOWN: #{result.status.inspect} #{result.inspect}" }
                end
              end
              # rubocop:enable Metrics/MethodLength
            end
          end
        end
      end
    end
  end
end

# frozen_string_literal: true

module Datadog
  module AppSec
    module Contrib
      module Sinatra
        module Reactive
          # Dispatch data from a Sinatra request to the WAF context
          module Routed
            def self.subscribe(op, waf_context)
              op.subscribe(*ADDRESSES) do |*values|
                Datadog.logger.debug { "reacted to #{ADDRESSES.inspect}: #{values.inspect}" }
                path_params = values[0]

                waf_args = {
                  'server.request.path_params' => path_params,
                }

                Datadog.logger.debug { "WAF ARGS: #{waf_args.inspect}" }

                waf_timeout = Datadog.configuration.appsec.waf_timeout
                result = waf_context.run(waf_args, waf_timeout)

                Datadog.logger.debug { "WAF TIMEOUT: #{result.inspect}" } if result.timeout

                case result.status
                when :match
                  Datadog.logger.debug { "WAF: #{result.inspect}" }

                  block = result.actions.include?('block')

                  yield [result, block]

                  throw(:block, [result, true]) if block
                when :ok
                  Datadog.logger.debug { "WAF OK: #{result.inspect}" }
                when :invalid_call
                  Datadog.logger.debug { "WAF CALL ERROR: #{result.inspect}" }
                when :invalid_rule, :invalid_flow, :no_rule
                  Datadog.logger.debug { "WAF RULE ERROR: #{result.inspect}" }
                else
                  Datadog.logger.debug { "WAF UNKNOWN: #{result.status.inspect} #{result.inspect}" }
                end
              end
            end
          end
        end
      end
    end
  end
end

module Datadog
  module AppSec
    # Core-pluggable component for AppSec
    class Component
      def initialize(processor:)
        @processor = processor
        pp " WAF NEW processor from init: #{@processor.inspect}"
        @mutex = Mutex.new
      end

      def reconfigure(ruleset:)
        @mutex.synchronize do
          new = Processor.new(ruleset: ruleset)

          if new && new.ready?
            old = @processor
            @processor = new
            pp " WAF NEW processor from rc: #{@processor.inspect}"
            old.finalize if old
          end
        end
      end
    end
  end
end

# frozen_string_literal: true

module Datadog
  module AppSec
    # Remote
    module Remote
      class << self
        # rubocop:disable Metrics/MethodLength
        def receivers
          puts " WAF GOT NEW APPSEC RC0! #{__LINE__}"
          return [] unless remote_features_enabled?
          puts " WAF GOT NEW APPSEC RC! #{__LINE__}"

          matcher = Core::Remote::Dispatcher::Matcher::Product.new(ASM_PRODUCTS)
          receiver = Core::Remote::Dispatcher::Receiver.new(matcher) do |repository, changes|
            changes.each do |change|
              Datadog.logger.debug { "remote config change: '#{change.path}'" }
            end

            rules = []
            custom_rules = []
            data = []
            overrides = []
            exclusions = []

            repository.contents.each do |content|
              parsed_content = parse_content(content)

              case content.path.product
              when 'ASM_DD'
                puts " WAF GOT NEW APPSEC RC! #{__LINE__}"
                rules << parsed_content
              when 'ASM_DATA'
                puts " WAF GOT NEW APPSEC RC! #{__LINE__}"
                data << parsed_content['rules_data'] if parsed_content['rules_data']
              when 'ASM'
                puts " WAF GOT NEW APPSEC RC! #{__LINE__}"
                overrides << parsed_content['rules_override'] if parsed_content['rules_override']
                exclusions << parsed_content['exclusions'] if parsed_content['exclusions']
                custom_rules << parsed_content['custom_rules'] if parsed_content['custom_rules']
              end
            end

            puts " WAF GOT NEW APPSEC RC! #{__LINE__}"
            if rules.empty?
              puts " WAF GOT NEW APPSEC RC! #{__LINE__}"
              settings_rules = AppSec::Processor::RuleLoader.load_rules(ruleset: Datadog.configuration.appsec.ruleset)

              raise NoRulesError, 'no default rules available' unless settings_rules

              rules = [settings_rules]
            end

            puts " WAF GOT NEW APPSEC RC! #{__LINE__}"
            ruleset = AppSec::Processor::RuleMerger.merge(
              rules: rules,
              data: data,
              overrides: overrides,
              exclusions: exclusions,
              custom_rules: custom_rules,
              )

            Datadog::AppSec.reconfigure(ruleset: ruleset)
          end

          puts " WAF GOT NEW APPSEC RC! #{__LINE__}"

          [receiver]
        end
        # rubocop:enable Metrics/MethodLength
      end
    end
  end
end

# frozen_string_literal: true


module Datadog
  module Core
    module Remote
      # Configures the HTTP transport to communicate with the agent
      # to fetch and sync the remote configuration
      class Component
        def initialize(settings, capabilities, agent_settings)
          puts " WAF component init! #{__LINE__}"
          transport_options = {}
          transport_options[:agent_settings] = agent_settings if agent_settings

          negotiation = Negotiation.new(settings, agent_settings)
          transport_v7 = Datadog::Core::Transport::HTTP.v7(**transport_options.dup)

          @barrier = Barrier.new(BARRIER_TIMEOUT)

          @client = Client.new(transport_v7, capabilities)
          healthy = false
          Datadog.logger.debug { "new remote configuration client: #{@client.id}" }

          @worker = Worker.new(interval: settings.remote.poll_interval_seconds) do
            puts " WAF worker run! #{__LINE__}"
            unless healthy || negotiation.endpoint?('/v0.7/config')
              puts " WAF worker run! #{__LINE__}"
              @barrier.lift

              next
            end

            begin
              puts " WAF worker run! #{__LINE__}"
              @client.sync
              puts " WAF worker run! #{__LINE__}"
              healthy ||= true
            rescue Client::SyncError => e
              puts " WAF worker run! #{__LINE__}"
              Datadog.logger.error do
                "remote worker client sync error: #{e.message} location: #{Array(e.backtrace).first}. skipping sync"
              end
            rescue StandardError => e
              puts " WAF worker run! #{__LINE__}"
              Datadog.logger.error do
                "remote worker error: #{e.class.name} #{e.message} location: #{Array(e.backtrace).first}. "\
                'reseting client state'
              end

              # client state is unknown, state might be corrupted
              @client = Client.new(transport_v7, capabilities)
              healthy = false
              Datadog.logger.debug { "new remote configuration client: #{@client.id}" }

              # TODO: bail out if too many errors?
            end

            puts " WAF worker run! #{__LINE__}"

            @barrier.lift
          end
        end

        # Starts the Remote Configuration worker without waiting for first run
        def start
          puts " WAF worker start! #{__LINE__}"
          @worker.start
        end

        # If the worker is not initialized, initialize it.
        #
        # Then, waits for one client sync to be executed if `kind` is `:once`.
        def barrier(kind)
          puts " WAF worker barrier! #{__LINE__}"
          start

          case kind
          when :once
            @barrier.wait_once
          end
        end

      end
    end
  end
end


require 'datadog/core/remote/client'


module Datadog
  module Core
    module Remote
      # Client communicates with the agent and sync remote configuration
      class Client
        def sync
          # TODO: Skip sync if no capabilities are registered
          response = transport.send_config(payload)

          if response.ok?
            # when response is completely empty, do nothing as in: leave as is
            if response.empty?
              Datadog.logger.debug { 'remote: empty response => NOOP' }

              return
            end

            begin
              paths = response.client_configs.map do |path|
                Configuration::Path.parse(path)
              end

              targets = Configuration::TargetMap.parse(response.targets)

              contents = Configuration::ContentList.parse(response.target_files)
            rescue Remote::Configuration::Path::ParseError => e
              raise SyncError, e.message
            end

            # To make sure steep does not complain
            return unless paths && targets && contents

            # TODO: sometimes it can strangely be so that paths.empty?
            # TODO: sometimes it can strangely be so that targets.empty?

            changes = repository.transaction do |current, transaction|
              # paths to be removed: previously applied paths minus ingress paths
              (current.paths - paths).each { |p| transaction.delete(p) }

              # go through each ingress path
              paths.each do |path|
                # match target with path
                target = targets[path]

                # abort entirely if matching target not found
                raise SyncError, "no target for path '#{path}'" if target.nil?

                # new paths are not in previously applied paths
                new = !current.paths.include?(path)

                # updated paths are in previously applied paths
                # but the content hash changed
                changed = current.paths.include?(path) && !current.contents.find_content(path, target)

                # skip if unchanged
                same = !new && !changed

                next if same

                # match content with path and target
                content = contents.find_content(path, target)

                puts " WAF worker check! #{paths.inspect}"
                puts " WAF worker check! #{target.inspect}"
                puts " WAF worker check! #{contents.inspect}"

                # abort entirely if matching content not found
                raise SyncError, "no valid content for target at path '#{path}'" if content.nil?

                # to be added or updated << config
                # TODO: metadata (hash, version, etc...)
                transaction.insert(path, target, content) if new
                transaction.update(path, target, content) if changed
              end

              # save backend opaque backend state
              transaction.set(opaque_backend_state: targets.opaque_backend_state)
              transaction.set(targets_version: targets.version)

              # upon transaction end, new list of applied config + metadata (add, change, remove) will be saved
              # TODO: also remove stale config (matching removed) from cache (client configs is exhaustive list of paths)
            end

            if changes.empty?
              Datadog.logger.debug { 'remote: no changes' }
            else
              dispatcher.dispatch(changes, repository)
            end
          end
        end
      end
    end
  end
end


# frozen_string_literal: true


module Datadog
  module Core
    module Remote
      class Configuration
        # Content stores the information associated with a specific Configuration::Path

        # ContentList stores a list of Conetnt instances
        # It provides convinient methods for finding content base on Configuration::Path and Configuration::Target
        class ContentList
          class << self
            def parse(array)
              new.concat(array.map { |c| Content.parse(c) })
            end
          end

          def find_content(path, target)
            puts " WAF worker check p! #{path.inspect}"
            puts " WAF worker check t! #{target.inspect}"
            puts " WAF worker check s! #{self.inspect}"
            find { |c| c.path.eql?(path) && target.check(c) }
          end

          def [](path)
            find { |c| c.path.eql?(path) }
          end

          def []=(path, content)
            map! { |c| c.path.eql?(path) ? content : c }
          end

          def delete(path)
            idx = index { |e| e.path.eql?(path) }

            return if idx.nil?

            delete_at(idx)
          end

          def paths
            map(&:path).uniq
          end
        end
      end
    end
  end
end

Datadog.configure do |c|
  c.diagnostics.debug = true
  require 'logger'
  c.logger.instance = ::Logger.new(STDOUT)

  unless c.respond_to?(:tracing)
    c.use :sinatra, service_name: (ENV['DD_SERVICE'] || 'sinatra')
  end
end

require 'rack/contrib/json_body_parser'
use Rack::JSONBodyParser

# Send non-web init event

if defined?(Datadog::Tracing)
  Datadog::Tracing.trace('init.service') { }
else
  Datadog.tracer.trace('init.service') { }
end

get '/' do
  pp request.env
  puts 'is this right?'
  STDOUT.flush
  'Hello, world!'
end

post '/' do
  puts 'or this right?'
  STDOUT.flush
  'Hello, world!'
end

get '/waf' do
  'Hello, world!'
end

post '/waf' do
  'Hello, world!'
end

get '/waf/:value' do
  'Hello, world!'
end

post '/waf/:value' do
  'Hello, world!'
end

get '/params/:value' do
  'Hello, world!'
end

get '/spans' do
  begin
    repeats = Integer(request.params['repeats'] || 0)
    garbage = Integer(request.params['garbage'] || 0)
  rescue ArgumentError
    response.status = 400

    'bad request'
  else
    repeats.times do |i|
      Datadog::Tracing.trace('repeat-#{i}') do |span|
        garbage.times do |j|
          span.set_tag("garbage-#{j}", "#{j}")
        end
      end
    end
  end

  'Generated #{repeats} spans with #{garbage} garbage tags'
end

get '/headers' do
  response.headers['Cache-Control'] = 'public, max-age=300'

  response.headers['Content-Type'] = 'text/plain'
  response.headers['Content-Length'] = '15'
  response.headers['Content-Language'] = 'en-US'

  'Hello, headers!'
end

get '/identify' do
  trace = Datadog::Tracing.active_trace
  trace.set_tag('usr.id', 'usr.id')
  trace.set_tag('usr.name', 'usr.name')
  trace.set_tag('usr.email', 'usr.email')
  trace.set_tag('usr.session_id', 'usr.session_id')
  trace.set_tag('usr.role', 'usr.role')
  trace.set_tag('usr.scope', 'usr.scope')

  'Hello, world!'
end

get '/status' do
  code = params['code'].to_i
  status code

  'Ok'
end

get '/make_distant_call' do
  content_type :json

  url = request.params["url"]
  uri = URI(url)
  request = nil
  response = nil

  Net::HTTP.start(uri.host, uri.port) do |http|
    request = Net::HTTP::Get.new(uri)

    response = http.request(request)
  end

  result = {
    "url": url,
    "status_code": response.code,
    "request_headers": request.each_header.to_h,
    "response_headers": response.each_header.to_h,
  }

  result.to_json
end

require 'datadog/kit/appsec/events'

get '/user_login_success_event' do
  Datadog::Kit::AppSec::Events.track_login_success(
    Datadog::Tracing.active_trace, user: {id: 'system_tests_user'}, metadata0: "value0", metadata1: "value1"
  )

  'Ok'
end

get '/user_login_failure_event' do
  Datadog::Kit::AppSec::Events.track_login_failure(
    Datadog::Tracing.active_trace, user_id: 'system_tests_user', user_exists: true, metadata0: "value0", metadata1: "value1"
  )

  'Ok'
end

get '/custom_event' do
  Datadog::Kit::AppSec::Events.track('system_tests_event', Datadog::Tracing.active_trace,  metadata0: "value0", metadata1: "value1")

  'Ok'
end

%i(get post options).each do |request_method|
  send(request_method, '/tag_value/*') do
    tag_value, status_code = request.path.split('/').select { |p| !p.empty? && p != 'tag_value' }
    trace = Datadog::Tracing.active_trace
    trace.set_tag("appsec.events.system_tests_appsec_event.value", tag_value)

    status status_code
    headers request.params || {}

    'Value tagged'
  end
end

get '/users' do
  user_id = request.params["user"]

  Datadog::Kit::Identity.set_user(id: user_id)

  'Hello, user!'
end

puts 'STRATED!'
STDOUT.flush

# frozen_string_literal: true







puts "XX"
STDOUT.flush

pp ENV.inspect


at_exit { STDOUT.flush; STDERR.flush }