require 'openstudio-analysis'

# SERVER_HOST = 'http://localhost:3000'
SERVER_HOST = 'http://bball-130590.nrel.gov:8080'

# ANALYSIS_ID =

# api = OpenStudio::Analysis::ServerApi.new(hostname: SERVER_HOST)
# if api.alive?
#   project_id = api.get_project_ids.last # This should be the last analysis that was run
#   analysis_id = api.get_analyses(project_id).last
#
#   Dir.mkdir analysis_id unless Dir.exist? analysis_id
#
#   puts "Processing results for analysis id: #{analysis_id}"
#
#   if api.get_analysis_status(analysis_id, 'batch_run') == 'completed'
#     results = api.get_analysis_results(analysis_id)
#
#     results[:data].each do |dp|
#       dir = "#{analysis_id}/#{dp[:_id]}"
#
#       Dir.mkdir dir unless Dir.exist? dir
#
#       # save off the JSON snippet into the new directory
#       File.open("#{dir}/variables.json", 'w') {|f| f << JSON.pretty_generate(dp)}
#
#       # save off the timeseries into the new directory
#       api.download_datapoint_report(dp[:_id], 'ambient_loop_reports_report_timeseries.csv', dir)
#     end
#   else
#     puts "Simulations are still running. Try again later"
#   end
# else
#   puts "Server is not running. Trying to process data using cached files"
# end

# Go through the directories and update the reports to add in the last column of data.
File.open('results.csv', 'w') do |new_file|
  Dir["**/*.csv"].each.with_index do |file, file_index|
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
          new_file << "#{line.chomp},#{new_header.join(',')}\n"
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