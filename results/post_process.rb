require 'openstudio-analysis'
require 'optparse'

options = {
  server: 'http://localhost:3000',
  download: false,
  post_process: false,
  analysis_id: nil
}

parser = OptionParser.new do|opts|
  opts.banner = "Usage: years.rb [options]"
  opts.on('-s', '--server host', 'Server Host URL') do |server|
    options[:server] = server;
  end

  opts.on('-a', '--analysis id', 'Analysis ID to Post Process') do |id|
    options[:analysis_id] = id;
  end

  opts.on('--download', 'Download Data') do
    options[:download] = true
  end

  opts.on('--post-process', 'Post Process Data') do
    options[:post_process] = true
  end
end
parser.parse!

unless options[:download] || options[:post_process]
  puts "Pass either --download or --post-process"
  exit
end

def post_process_analysis_id(analysis_id)
  # Go through the directories and update the reports to add in the last column of data.
  File.open("#{analysis_id}/results.csv", 'w') do |new_file|
    Dir["#{analysis_id}/**/*.csv"].each.with_index do |file, file_index|
      puts "Processing file #{file}"
      dir = File.dirname(file)
      json_file = "#{dir}/variables.json"
      puts json_file
      if File.exist? json_file
        json = JSON.parse(File.read(json_file))
        new_header = []
        new_data = []
        json.keys.each do |key|
          next if ['name', 'status', 'data_point_uuid', 'run_start_time', 'run_end_time', 'status_message'].include? key
          new_header << key
          new_data << json[key]
        end

        # puts "New data are: #{new_header} : #{new_data}"
        File.readlines(file).each.with_index do |line, index|
          if file_index.zero? && index.zero?
            # write out the header into the new file
            new_file << "#{line.gsub(' ','').chomp},#{new_header.join(',')}\n"
          elsif index.zero?
            # ignore the headers in the other files
            next
          else
            new_file << "#{line.chomp},#{new_data.join(',')}\n"
          end
        end
      end
    end
  end
end


if options[:download]
  api = OpenStudio::Analysis::ServerApi.new(hostname: options[:server])
  if api.alive?
    project_id = api.get_project_ids.last # This should be the last analysis that was run
    analysis_id = api.get_analyses(project_id).last

    Dir.mkdir analysis_id unless Dir.exist? analysis_id

    puts "Processing results for analysis id: #{analysis_id}"

    if api.get_analysis_status(analysis_id, 'batch_run') == 'completed'
      results = api.get_analysis_results(analysis_id)

      results[:data].each do |dp|
        dir = "#{analysis_id}/#{dp[:_id]}"

        Dir.mkdir dir unless Dir.exist? dir

        # save off the JSON snippet into the new directory
        File.open("#{dir}/variables.json", 'w') {|f| f << JSON.pretty_generate(dp)}

        # save off the timeseries into the new directory
        api.download_datapoint_report(dp[:_id], 'ambient_loop_reports_report_timeseries.csv', dir)
      end
    else
      puts "Simulations are still running. Try again later"
    end
  else
    puts "Server is not running. Trying to process data using cached files"
  end
end

if options[:post_process]
  if options[:analysis_id]
    post_process_analysis_id(options[:analysis_id])
  else
    puts "No analysis_id passed, post processing all the results"
    Dir['*'].select {|f| File.directory? f}.each do |dir|
      post_process_analysis_id(dir)
    end
  end
end

