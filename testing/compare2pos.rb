#!/usr/bin/env ruby

require 'digest'

files = {
	"sediment" => {
		"lines" => Array.new,
		"blocks" => Hash.new,
		"src" => ARGV[0],
	},
	"compare" => {
		"lines" => Array.new,
		"blocks" => Hash.new,
		"src" => ARGV[1],
	},
}

[ "sediment", "compare" ].each { |n|
	lc = 0
	File.open(files[n]["src"]).each { |line|
		lc += 1
		# puts "Got line: #{lc}"
		files[n]["lines"].push line
	}
	tmp_block = Array.new
	prefix = ""
	inside_msgstr = false
	files[n]["lines"].each { |line|
		if inside_msgstr == false
			if line =~ /^msgstr/
				inside_msgstr = true
			else
				prefix = prefix + line
			end
		end
		if line.strip.size < 1
			# puts prefix
			hsh = Digest::SHA1.hexdigest(prefix)
			# puts "Got hash: #{hsh}"
			files[n]["blocks"][hsh] = tmp_block
			tmp_block = Array.new
			prefix = ""
			inside_msgstr = false
		else
			tmp_block.push line.strip
		end
	}
}
	
# Now compare all hashes:

matches = 0

files["sediment"]["blocks"].each { |h,b|
	if files["compare"]["blocks"].has_key? h
		matches += 1
		files["compare"]["blocks"][h].each { |l|
			puts l.strip
		}
		puts
	end
}

puts "Could identify #{matches} matching blocks"
