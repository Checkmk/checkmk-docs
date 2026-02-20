#!/usr/bin/env ruby

def write_block(handle, block)
	block.each { |line|
		handle.write line + "\n"
	}
	handle.write "\n"
end

def nonempty_msgstr(block)
	msgstr_inside = false
	strlen = 0
	block.each { |line|
		if line =~ /msgstr.*?"(.*?)"/
			msgstr_inside = true
			strlen += $1.size
		end
		if msgstr_inside == true && line =~ /"(.*?)"/
			strlen += $1.size
		end
	}
	puts "Message string has #{strlen} characters"
	return true if strlen > 0
	return false
end

lines = Array.new
blocks = Array.new

File.open(ARGV[0]).each { |line| lines.push line }

tmp_block = Array.new
lines.each { |line|
	if line.strip.size < 1
		blocks.push tmp_block
		tmp_block = Array.new
	else
		tmp_block.push line.strip
	end
}

goodcount = 0
goodfile = File.new(ARGV[1], "w")
badcount = 0
badfile = File.new(ARGV[2], "w")

write_block(goodfile, blocks[0])
write_block(badfile, blocks[0])

bcount = 0
1.upto(blocks.size - 1) { |n|
	blocks[n].each { |line|
		puts line
	}
	if nonempty_msgstr(blocks[n])
		write_block(badfile, blocks[n])
		badcount += 1
	else
		write_block(goodfile, blocks[n])
		goodcount += 1
	end
	puts "===>8======================"
}

puts "Written #{goodcount} entries to good file"
puts "Written #{badcount} entries to bad file"
