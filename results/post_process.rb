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
    options[:server] = server
  end

  opts.on('-a', '--analysis id', 'Analysis ID to Download or Post Process') do |id|
    options[:analysis_id] = id
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

if options[:download] && !options[:analysis_id]
  puts "If --download, then must pass analysis_id to download (e.g. -a <id> --download)"
  exit
end

def post_process_analysis_id(analysis_id)
  save_dir = "../python/output/#{analysis_id}/"
  FileUtils.mkdir_p save_dir
  # Go through the directories and update the reports to add in the last column of data.
  File.open("#{save_dir}/simulation_results.csv", 'w') do |new_file|
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

    Dir.mkdir options[:analysis_id] unless Dir.exist? options[:analysis_id]

    puts "Downloading results for analysis id: #{options[:analysis_id]}"

    if api.get_analysis_status(options[:analysis_id], 'batch_run') == 'completed'
      results = api.get_analysis_results(options[:analysis_id])

      results[:data].each do |dp|
        dir = "#{options[:analysis_id]}/#{dp[:_id]}"
        puts "Saving results for simulation into directory: #{dir}"

        Dir.mkdir dir unless Dir.exist? dir

        # save off the JSON snippet into the new directory
        File.open("#{dir}/variables.json", 'w') {|f| f << JSON.pretty_generate(dp)}

        # save off the timeseries into the new directory
        api.download_datapoint_report(dp[:_id], 'ambient_loop_reports_report_timeseries.csv', dir)
        api.download_datapoint(dp[:_id], dir)
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

