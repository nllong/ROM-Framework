require 'openstudio-analysis'
require 'optparse'
require 'date'

options = {
    server: 'http://localhost:3000',
    download: false,
    post_process: false,
    analysis_id: nil,
    rename_to: nil
}

parser = OptionParser.new do |opts|
  opts.banner = "Usage: post_process.rb [options]"
  opts.on('-s', '--server host', 'Server Host URL') do |server|
    options[:server] = server
  end

  opts.on('-a', '--analysis id', 'Analysis ID to Download or Dir Name to Post Process') do |id|
    options[:analysis_id] = id
  end

  opts.on('-r', '--rename-to name', 'Rename download directory to <name> (no spaces)') do |rename_to|
    options[:rename_to] = rename_to
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
  save_dir = analysis_id
  FileUtils.mkdir_p save_dir
  # Go through the directories and update the reports to add in the last column of data.
  File.open("#{save_dir}/simulation_results.csv", 'w') do |new_file|
    heat_mass_flow_index = nil
    cool_mass_flow_index = nil
    Dir["#{analysis_id}/*/*.csv"].each.with_index do |file, file_index|
      puts "Processing file #{file}"
      dir = File.dirname(file)
      new_header = []
      new_data = []

      json_file = "#{dir}/variables.json"
      # add in the variables JSON
      if File.exist? json_file
        json = JSON.parse(File.read(json_file))
        json.keys.each do |key|
          next if ['name', 'status', 'data_point_uuid', 'status_message', 'internal_loads_multiplier.epd_multiplier', 'internal_loads_multiplier.lpd_multiplier'].include? key
          new_header << key
          new_data << json[key]
        end
      end

      json_file = "#{dir}/results.json"
      if File.exist? json_file
        json = JSON.parse(File.read(json_file))
        json.keys.each do |measure_name|
          if ['internal_loads_multiplier'].include? measure_name
            new_header << 'lpd_average'
            new_header << 'epd_average'
            new_header << 'ppl_average'

            new_data << json[measure_name]['lpd_average']
            new_data << json[measure_name]['epd_average']
            new_data << json[measure_name]['ppl_average']
          end
        end
      end

      # puts "New data are: #{new_header} : #{new_data}"
      File.readlines(file).each.with_index do |line, index|
        if file_index.zero? && index.zero?
          # get the index of few variables to create other indicators for
          # specific models
          new_header << 'hvac_mode'
          line_split = line.split(',')
          heat_mass_flow_index = line_split.find_index('District Heating Mass Flow Rate')
          cool_mass_flow_index = line_split.find_index('District Cooling Mass Flow Rate')

          # write out the header into the new file
          new_file << "#{line.gsub(' ', '').chomp},#{new_header.join(',')}\n"
        elsif index.zero?
          # ignore the headers in the other files
          next
        else
          line_split = line.split(',')
          heat_value = line_split[heat_mass_flow_index].to_f
          cool_value = line_split[cool_mass_flow_index].to_f
          hvac_mode = 0
          if heat_value > 0 && cool_value > 0
            hvac_mode = 3
          elsif heat_value > 0
            hvac_mode = 1
          elsif cool_value > 0
            hvac_mode = 2
          end

          new_file << "#{line.chomp},#{new_data.join(',')},#{hvac_mode}\n"
        end
      end
    end
  end

  # generate summary statistics on the simulations
  File.open("#{save_dir}/summary.csv", 'w') do |out_file|
    Dir["#{analysis_id}/*/*.osw"].each.with_index do |file, file_index|
      headers = ["index", "uuid", "total_runtime", "energyplus_runtime", "total_measure_runtime", "other_runtime", "number_of_measures"]
      dir = File.dirname(file)
      json = JSON.parse(File.read(file))

      # The first file sets the length of the measures!
      if file_index.zero?
        json['steps'].each do |h|
          headers << "#{h['name']}_runtime"
        end
      end

      new_data = []
      new_data << file_index
      new_data << json['osd_id']
      start_time = DateTime.parse(json['started_at'])
      completed_at = DateTime.parse(json['completed_at'])
      total_time = completed_at.to_time - start_time.to_time
      new_data << total_time

      # read in the results.json
      json_file = "#{dir}/results.json"
      energyplus_runtime = 9999
      if File.exist? json_file
        results_json = JSON.parse(File.read(json_file))
        energyplus_runtime = results_json['ambient_loop_reports']['energyplus_runtime']
        new_data << energyplus_runtime
      else
        new_data << 'unknown ep runtime'
      end

      total_measure_time = 0
      measure_run_times = []
      json['steps'].each do |h|
        start_time = DateTime.parse(h['result']['started_at'])
        completed_at = DateTime.parse(h['result']['completed_at'])
        delta_time = completed_at.to_time - start_time.to_time
        total_measure_time += delta_time
        measure_run_times << delta_time
      end
      new_data << total_measure_time
      new_data << total_time - energyplus_runtime - total_measure_time
      new_data << json['steps'].size
      new_data += measure_run_times

      out_file << "#{headers.join(',')}\n" if file_index.zero?
      out_file << "#{new_data.join(',')}\n"
    end
  end

end


if options[:download]
  api = OpenStudio::Analysis::ServerApi.new(hostname: options[:server])
  if api.alive?
    project_id = api.get_project_ids.last # This should be the last analysis that was run

    base_dir = options[:rename_to].nil? ? options[:analysis_id] : options[:rename_to]
    puts base_dir
    if Dir.exist? base_dir
        raise "Directory exists, remove first or change/add rename_to"
    else
        Dir.mkdir base_dir
    end

    puts "Downloading results for analysis id: #{options[:analysis_id]}"

    if api.get_analysis_status(options[:analysis_id], 'batch_run') == 'completed'
      results = api.get_analysis_results(options[:analysis_id])
      results[:data].each do |dp|
        dir = "#{base_dir}/#{dp[:_id]}"
        puts "Saving results for simulation into directory: #{dir}"
        Dir.mkdir dir unless Dir.exist? dir

        # save off the JSON snippet into the new directory
        File.open("#{dir}/variables.json", 'w') {|f| f << JSON.pretty_generate(dp)}

        # grab the datapoint json, and save off the results (which contain some of the resulting covariates)
        results = api.get_datapoint(dp[:_id])
        File.open("#{dir}/results.json", 'w') {|f| f << JSON.pretty_generate(results[:data_point][:results])}

        # save off some of the results: timeseries, datapoint json, and out.osw
        api.download_datapoint_report(dp[:_id], 'ambient_loop_reports_report_timeseries.csv', dir)
        api.download_datapoint_report(dp[:_id], 'out.osw', dir)
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

